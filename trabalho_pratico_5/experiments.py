"""Experimentos locais reproduzíveis entre agentes, sem chamadas à API."""

from __future__ import annotations

import argparse
import json
import random
import time
from collections import Counter
from typing import Any

from agents import HeuristicAgent
from game import BLACK, Othello


class RandomAgent:
    name = "Aleatório"

    def __init__(self, seed: int) -> None:
        self.random = random.Random(seed)

    def play_turn(self, game: Othello) -> None:
        moves = game.get_valid_moves()
        if not moves:
            raise ValueError("O agente não recebeu uma posição com jogadas legais.")
        row, col = self.random.choice(moves)
        game.make_move(game.current_player, row, col)


def play_game(black_agent: Any, white_agent: Any) -> dict[str, Any]:
    game = Othello()
    elapsed: list[float] = []
    while not game.is_game_over():
        agent = black_agent if game.current_player == BLACK else white_agent
        started = time.perf_counter()
        agent.play_turn(game)
        elapsed.append(time.perf_counter() - started)

    status = game.get_game_status()
    winner = status["winner"]
    return {
        "winner": "black" if winner == BLACK else "white" if winner == -BLACK else "draw",
        "score": status["score"],
        "moves": status["moves_played"],
        "mean_seconds_per_move": sum(elapsed) / len(elapsed) if elapsed else 0.0,
    }


def run_experiments(games: int = 20, seed: int = 128) -> dict[str, Any]:
    if games < 1:
        raise ValueError("O número de partidas deve ser pelo menos 1.")

    results: list[dict[str, Any]] = []
    heuristic = HeuristicAgent()
    for game_number in range(games):
        rng = random.Random(seed + game_number)
        random_agent = RandomAgent(rng.randrange(2**32))
        if game_number % 2 == 0:
            result = play_game(heuristic, random_agent)
            result["black_agent"], result["white_agent"] = "Heurístico", "Aleatório"
        else:
            result = play_game(random_agent, heuristic)
            result["black_agent"], result["white_agent"] = "Aleatório", "Heurístico"
        results.append(result)

    wins = Counter()
    for result in results:
        if result["winner"] == "draw":
            wins["Empate"] += 1
        elif result["winner"] == "black":
            wins[result["black_agent"]] += 1
        else:
            wins[result["white_agent"]] += 1
    return {
        "games": games,
        "seed": seed,
        "summary": {
            "heuristic_wins": wins["Heurístico"],
            "random_wins": wins["Aleatório"],
            "draws": wins["Empate"],
            "heuristic_win_rate": wins["Heurístico"] / games,
            "mean_moves": sum(result["moves"] for result in results) / games,
            "mean_seconds_per_move": sum(
                result["mean_seconds_per_move"] for result in results
            ) / games,
        },
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--games", type=int, default=20)
    parser.add_argument("--seed", type=int, default=128)
    args = parser.parse_args()
    print(json.dumps(run_experiments(args.games, args.seed), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
