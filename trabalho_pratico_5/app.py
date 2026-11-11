"""Interface Streamlit para jogar Othello contra agentes."""

from __future__ import annotations

import os

import streamlit as st

from agents import GroqAgent, HeuristicAgent, MODEL_DEFAULT, MoveDecision
from game import BLACK, WHITE, Othello

st.set_page_config(page_title="Agentes de Othello", page_icon="⚫", layout="wide")
st.title("Othello — Agentes Inteligentes")
st.caption("Jogo 8×8 com regras locais, agente Groq e estratégia heurística.")

if "game" not in st.session_state:
    st.session_state.game = Othello()
if "mode" not in st.session_state:
    st.session_state.mode = "Humano × Groq"
if "groq_calls" not in st.session_state:
    st.session_state.groq_calls = 0
if "groq_latency_seconds" not in st.session_state:
    st.session_state.groq_latency_seconds = 0.0

with st.sidebar:
    st.header("Configuração")
    mode = st.selectbox(
        "Modo de jogo",
        ["Humano × Groq", "Groq × Heurístico", "Heurístico × Heurístico"],
        key="mode",
    )
    model_name = st.text_input("Modelo Groq", value=os.getenv("GROQ_MODEL", MODEL_DEFAULT))
    api_key = st.text_input(
        "Chave de API Groq",
        value=os.getenv("GROQ_API_KEY", ""),
        type="password",
        help="Usada somente nesta sessão; não a salve no notebook nem no código.",
    )
    if st.button("Nova partida", use_container_width=True):
        st.session_state.game = Othello()
        st.session_state.groq_calls = 0
        st.session_state.groq_latency_seconds = 0.0
        st.rerun()

game: Othello = st.session_state.game
status = game.get_game_status()
player_names = {BLACK: "Pretas", WHITE: "Brancas"}
st.subheader(
    "Partida encerrada" if status["game_over"]
    else f"Vez das {player_names[game.current_player]}"
)
st.write(f"⚫ Pretas: **{status['score']['black']}**  ·  ⚪ Brancas: **{status['score']['white']}**")
st.sidebar.metric("Chamadas Groq nesta partida", st.session_state.groq_calls)
st.sidebar.metric(
    "Tempo acumulado do LLM",
    f"{st.session_state.groq_latency_seconds:.2f} s",
)


def play_groq_turn() -> MoveDecision:
    agent = GroqAgent(api_key=api_key, model=model_name)
    decision = agent.play_turn(game)
    st.session_state.groq_calls += agent.calls
    st.session_state.groq_latency_seconds += agent.llm_latency_seconds
    return decision

legal_moves = set(game.get_valid_moves())
clicked_move: tuple[int, int] | None = None
columns = st.columns(8, gap="small")
for row in range(8):
    for col, column in enumerate(columns):
        value = game.board[row][col]
        symbol = "⚫" if value == BLACK else "⚪" if value == WHITE else "·"
        is_human_turn = mode == "Humano × Groq" and game.current_player == BLACK
        enabled = not status["game_over"] and is_human_turn and (row, col) in legal_moves
        if column.button(
            symbol,
            key=f"square-{row}-{col}",
            disabled=not enabled,
            use_container_width=True,
            help=f"Linha {row + 1}, coluna {col + 1}",
        ):
            clicked_move = (row, col)

if clicked_move is not None:
    game.make_move(game.current_player, *clicked_move)
    st.rerun()

if status["game_over"]:
    winner = status["winner"]
    if winner == 0:
        st.success("Empate!")
    else:
        st.success(f"Vitória das {player_names[winner]}!")
elif mode != "Humano × Groq":
    if st.button("Próxima jogada", type="primary"):
        if mode == "Heurístico × Heurístico":
            agent = HeuristicAgent()
        elif game.current_player == BLACK:
            if not api_key:
                st.error("Informe a chave da API Groq na barra lateral.")
                st.stop()
            decision = play_groq_turn()
            st.info(f"Groq: {decision.reason}")
            st.rerun()
        else:
            agent = HeuristicAgent()
        decision = agent.play_turn(game)
        if decision:
            st.info(f"{agent.name}: {decision.reason}")
        st.rerun()
elif game.current_player == WHITE and not status["game_over"]:
    if st.button("Jogar com Groq", type="primary"):
        if not api_key:
            st.error("Informe a chave da API Groq na barra lateral.")
            st.stop()
        decision = play_groq_turn()
        st.info(f"Groq escolheu ({decision.row + 1}, {decision.col + 1}): {decision.reason}")
        st.rerun()

with st.expander("Histórico da partida"):
    for index, event in enumerate(game.history, start=1):
        if event.get("pass"):
            st.write(f"{index}. Jogador {event['player']} passou (sem jogadas válidas).")
        else:
            row, col = event["move"]
            st.write(
                f"{index}. Jogador {event['player']}: "
                f"linha {row + 1}, coluna {col + 1}; "
                f"{len(event['flipped'])} peça(s) virada(s)."
            )
