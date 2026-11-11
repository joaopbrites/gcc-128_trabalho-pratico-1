"""Agentes locais e agente Groq estruturado com LangGraph e tools."""

from __future__ import annotations

import json
import os
import time
from typing import Any, TypedDict

from langchain_core.tools import BaseTool, tool
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

from game import BLACK, WHITE, Move, Othello

MODEL_DEFAULT = "openai/gpt-oss-20b"
POSITION_WEIGHTS = (
    (100, -25, 10, 5, 5, 10, -25, 100),
    (-25, -45, -5, -5, -5, -5, -45, -25),
    (10, -5, 5, 2, 2, 5, -5, 10),
    (5, -5, 2, 1, 1, 2, -5, 5),
    (5, -5, 2, 1, 1, 2, -5, 5),
    (10, -5, 5, 2, 2, 5, -5, 10),
    (-25, -45, -5, -5, -5, -5, -45, -25),
    (100, -25, 10, 5, 5, 10, -25, 100),
)


class MoveDecision(BaseModel):
    row: int = Field(ge=0, le=7, description="Linha da jogada, de 0 a 7.")
    col: int = Field(ge=0, le=7, description="Coluna da jogada, de 0 a 7.")
    reason: str = Field(description="Justificativa breve da escolha.")


def create_game_tools(game: Othello) -> dict[str, BaseTool]:
    """Cria tools isoladas e vinculadas à partida recebida."""

    @tool
    def get_board_state() -> str:
        """Consulta o tabuleiro atual; células são 1 (preto), -1 (branco) ou 0."""
        return json.dumps(game.get_board_state())

    @tool
    def get_valid_moves() -> str:
        """Lista as jogadas válidas do jogador da vez como pares [linha, coluna]."""
        return json.dumps(game.get_valid_moves())

    @tool
    def make_move(row: int, col: int) -> str:
        """Executa uma jogada legal para o jogador da vez."""
        player = game.current_player
        flipped = game.make_move(player, row, col)
        return json.dumps({
            "player": player,
            "move": [row, col],
            "flipped": [list(move) for move in flipped],
        })

    @tool
    def get_game_status() -> str:
        """Consulta término, vencedor, marcador, turno e histórico da partida."""
        return json.dumps(game.get_game_status())

    return {
        "get_board_state": get_board_state,
        "get_valid_moves": get_valid_moves,
        "make_move": make_move,
        "get_game_status": get_game_status,
    }


class HeuristicAgent:
    """Agente determinístico que pondera posições, mobilidade e material."""

    name = "Heurístico"

    @staticmethod
    def _evaluate(board: list[list[int]], player: int) -> int:
        positional = sum(
            POSITION_WEIGHTS[row][col] * board[row][col] * player
            for row in range(8)
            for col in range(8)
        )
        material = sum(
            board[row][col] == player for row in range(8) for col in range(8)
        ) - sum(board[row][col] == -player for row in range(8) for col in range(8))
        return positional + material

    def choose_move(self, game: Othello) -> MoveDecision:
        player = game.current_player
        legal_moves = game.get_valid_moves(player)
        if not legal_moves:
            raise ValueError("O agente não recebeu uma posição com jogadas legais.")

        evaluated: list[tuple[int, Move]] = []
        for row, col in legal_moves:
            candidate = Othello()
            candidate.board = game.get_board_state()
            candidate.current_player = player
            candidate.make_move(player, row, col)
            mobility = len(candidate.get_valid_moves(-player))
            score = self._evaluate(candidate.board, player) - 7 * mobility
            evaluated.append((score, (row, col)))

        score, move = max(evaluated, key=lambda item: (item[0], -item[1][0], -item[1][1]))
        return MoveDecision(
            row=move[0],
            col=move[1],
            reason=f"Maior avaliação posicional e de mobilidade (pontuação {score}).",
        )

    def play_turn(self, game: Othello) -> MoveDecision:
        decision = self.choose_move(game)
        game.make_move(game.current_player, decision.row, decision.col)
        return decision


class DecisionState(TypedDict, total=False):
    game: Othello
    tools: dict[str, BaseTool]
    observation: dict[str, Any]
    decision: MoveDecision


class GroqAgent:
    """Agente LLM que consulta tools, decide via LangGraph e executa a jogada."""

    name = "Groq"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        llm: Any | None = None,
    ) -> None:
        self.model_name = model or os.getenv("GROQ_MODEL", MODEL_DEFAULT)
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if llm is None:
            if not self.api_key:
                raise ValueError(
                    "Configure GROQ_API_KEY no ambiente ou informe uma chave ao agente."
                )
            llm = ChatGroq(
                model=self.model_name,
                api_key=self.api_key,
                temperature=0,
                max_tokens=256,
                max_retries=2,
                timeout=30,
            )
        self.llm = llm
        self.structured_llm = self.llm.with_structured_output(MoveDecision)
        self.calls = 0
        self.llm_latency_seconds = 0.0

    def play_turn(self, game: Othello) -> MoveDecision:
        """Executa observar → analisar → validar → agir em um grafo LangGraph."""
        tools = create_game_tools(game)

        def observe(state: DecisionState) -> dict[str, Any]:
            board = json.loads(tools["get_board_state"].invoke({}))
            legal_moves = json.loads(tools["get_valid_moves"].invoke({}))
            status = json.loads(tools["get_game_status"].invoke({}))
            if not legal_moves:
                raise ValueError("O jogo não possui jogadas válidas para o turno.")
            return {
                "observation": {
                    "board": board,
                    "valid_moves": legal_moves,
                    "status": status,
                }
            }

        def decide(state: DecisionState) -> dict[str, Any]:
            observation = state["observation"]
            player = observation["status"]["current_player"]
            recent_history = observation["status"]["history"][-8:]
            self.calls += 1
            started = time.perf_counter()
            try:
                response = self.structured_llm.invoke([
                    SystemMessage(
                        content=(
                            "Você é um agente de Othello. Escolha exatamente uma jogada "
                            "da lista legal. Considere cantos, mobilidade e posições "
                            "estratégicas; não invente coordenadas. Responda com row, "
                            "col e uma justificativa curta em português."
                        )
                    ),
                    HumanMessage(content=json.dumps({
                        "jogador": "preto" if player == BLACK else "branco",
                        "tabuleiro": observation["board"],
                        "jogadas_validas": observation["valid_moves"],
                        "historico_recente": recent_history,
                    }, ensure_ascii=False)),
                ])
            finally:
                self.llm_latency_seconds += time.perf_counter() - started
            return {"decision": response}

        def validate(state: DecisionState) -> dict[str, Any]:
            decision = state["decision"]
            if [decision.row, decision.col] not in state["observation"]["valid_moves"]:
                raise ValueError(
                    f"Groq sugeriu ({decision.row}, {decision.col}), que não é "
                    "uma jogada legal. Nenhuma jogada foi executada."
                )
            return {}

        def execute(state: DecisionState) -> dict[str, Any]:
            decision = state["decision"]
            tools["make_move"].invoke({"row": decision.row, "col": decision.col})
            return {}

        graph = StateGraph(DecisionState)
        graph.add_node("observe", observe)
        graph.add_node("decide", decide)
        graph.add_node("validate", validate)
        graph.add_node("execute", execute)
        graph.set_entry_point("observe")
        graph.add_edge("observe", "decide")
        graph.add_edge("decide", "validate")
        graph.add_edge("validate", "execute")
        graph.add_edge("execute", END)
        final_state = graph.compile().invoke({"game": game, "tools": tools})
        return final_state["decision"]
