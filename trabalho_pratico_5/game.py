"""Regras e estado do jogo Othello (Reversi)."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

BOARD_SIZE = 8
EMPTY = 0
BLACK = 1
WHITE = -1
Move = tuple[int, int]

DIRECTIONS: tuple[Move, ...] = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),             (0, 1),
    (1, -1),  (1, 0),   (1, 1),
)


class Othello:
    """Estado mutável de uma partida, com validação completa das regras."""

    def __init__(self) -> None:
        self.board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.board[3][3] = WHITE
        self.board[4][4] = WHITE
        self.board[3][4] = BLACK
        self.board[4][3] = BLACK
        self.current_player = BLACK
        self.history: list[dict[str, Any]] = []

    @staticmethod
    def _validate_player(player: int) -> None:
        if player not in (BLACK, WHITE):
            raise ValueError("O jogador deve ser BLACK (1) ou WHITE (-1).")

    @staticmethod
    def _inside(row: int, col: int) -> bool:
        return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE

    def _flips_for_move(self, player: int, row: int, col: int) -> list[Move]:
        self._validate_player(player)
        if not self._inside(row, col) or self.board[row][col] != EMPTY:
            return []

        flips: list[Move] = []
        for dr, dc in DIRECTIONS:
            line: list[Move] = []
            r, c = row + dr, col + dc
            while self._inside(r, c) and self.board[r][c] == -player:
                line.append((r, c))
                r += dr
                c += dc
            if line and self._inside(r, c) and self.board[r][c] == player:
                flips.extend(line)
        return flips

    def get_valid_moves(self, player: int | None = None) -> list[Move]:
        """Retorna as coordenadas legais para o jogador indicado."""
        player = self.current_player if player is None else player
        self._validate_player(player)
        return [
            (row, col)
            for row in range(BOARD_SIZE)
            for col in range(BOARD_SIZE)
            if self._flips_for_move(player, row, col)
        ]

    def make_move(self, player: int, row: int, col: int) -> list[Move]:
        """Executa uma jogada legal e retorna as peças que foram viradas."""
        self._validate_player(player)
        if self.is_game_over():
            raise ValueError("A partida já terminou.")
        if player != self.current_player:
            raise ValueError("Não é o turno desse jogador.")

        flips = self._flips_for_move(player, row, col)
        if not flips:
            raise ValueError(f"Jogada inválida: ({row}, {col}).")

        self.board[row][col] = player
        for r, c in flips:
            self.board[r][c] = player
        self.history.append({
            "player": player,
            "move": (row, col),
            "flipped": tuple(flips),
        })

        next_player = -player
        if self.get_valid_moves(next_player):
            self.current_player = next_player
        elif self.get_valid_moves(player):
            self.history.append({"player": next_player, "pass": True})
            self.current_player = player
        else:
            self.current_player = next_player
        return flips

    def is_game_over(self) -> bool:
        """A partida termina quando o tabuleiro enche ou ninguém pode jogar."""
        if all(cell != EMPTY for row in self.board for cell in row):
            return True
        return not self.get_valid_moves(BLACK) and not self.get_valid_moves(WHITE)

    def get_board_state(self) -> list[list[int]]:
        """Devolve uma cópia do tabuleiro, sem expor o estado interno."""
        return deepcopy(self.board)

    def get_score(self) -> dict[str, int]:
        black = sum(cell == BLACK for row in self.board for cell in row)
        white = sum(cell == WHITE for row in self.board for cell in row)
        return {"black": black, "white": white, "empty": 64 - black - white}

    def get_game_status(self) -> dict[str, Any]:
        score = self.get_score()
        game_over = self.is_game_over()
        winner = None
        if game_over:
            winner = BLACK if score["black"] > score["white"] else WHITE
            if score["black"] == score["white"]:
                winner = 0
        return {
            "game_over": game_over,
            "winner": winner,
            "score": score,
            "current_player": self.current_player,
            "valid_moves": self.get_valid_moves() if not game_over else [],
            "moves_played": sum(not item.get("pass", False) for item in self.history),
            "history": deepcopy(self.history),
        }
