import unittest

from agents import GroqAgent, MoveDecision
from game import BLACK, WHITE, Othello


class FakeStructuredModel:
    def __init__(self, decision):
        self.decision = decision

    def invoke(self, messages):
        return self.decision


class FakeChatModel:
    def __init__(self, decision):
        self.structured_model = FakeStructuredModel(decision)

    def with_structured_output(self, schema):
        return self.structured_model


class OthelloTests(unittest.TestCase):
    def test_initial_position_has_four_legal_moves(self):
        game = Othello()
        self.assertEqual(game.get_valid_moves(BLACK), [(2, 3), (3, 2), (4, 5), (5, 4)])
        self.assertEqual(game.get_valid_moves(WHITE), [(2, 4), (3, 5), (4, 2), (5, 3)])

    def test_move_flips_pieces_and_changes_turn(self):
        game = Othello()
        flipped = game.make_move(BLACK, 2, 3)
        self.assertEqual(flipped, [(3, 3)])
        self.assertEqual(game.board[2][3], BLACK)
        self.assertEqual(game.board[3][4], BLACK)
        self.assertEqual(game.current_player, WHITE)

    def test_invalid_moves_do_not_change_board(self):
        game = Othello()
        original = game.get_board_state()
        with self.assertRaises(ValueError):
            game.make_move(BLACK, 0, 0)
        self.assertEqual(game.get_board_state(), original)
        with self.assertRaises(ValueError):
            game.make_move(WHITE, 2, 4)

    def test_board_state_is_a_copy(self):
        game = Othello()
        snapshot = game.get_board_state()
        snapshot[0][0] = BLACK
        self.assertEqual(game.board[0][0], 0)

    def test_game_ends_when_board_is_full(self):
        game = Othello()
        game.board = [[BLACK for _ in range(8)] for _ in range(8)]
        status = game.get_game_status()
        self.assertTrue(status["game_over"])
        self.assertEqual(status["winner"], BLACK)
        self.assertEqual(status["score"]["black"], 64)

    def test_game_ends_when_neither_player_can_move(self):
        game = Othello()
        game.board = [[BLACK for _ in range(8)] for _ in range(8)]
        game.board[0][0] = 0
        self.assertTrue(game.is_game_over())

    def test_forced_pass_keeps_turn_with_player_who_can_move(self):
        game = Othello()
        game.board = [[WHITE for _ in range(8)] for _ in range(8)]
        game.board[0][0] = 0
        game.board[0][1] = BLACK
        game.board[0][2] = WHITE
        game.board[0][4] = 0
        game.board[0][5] = BLACK
        game.board[0][6] = WHITE
        game.current_player = WHITE
        game.make_move(WHITE, 0, 4)
        self.assertEqual(game.current_player, WHITE)
        self.assertTrue(game.history[-1]["pass"])
        self.assertEqual(game.get_valid_moves(WHITE), [(0, 0)])

    def test_langgraph_agent_uses_tools_and_executes_legal_decision(self):
        game = Othello()
        model = FakeChatModel(MoveDecision(row=2, col=3, reason="Captura central."))
        agent = GroqAgent(llm=model)

        decision = agent.play_turn(game)

        self.assertEqual((decision.row, decision.col), (2, 3))
        self.assertEqual(game.board[2][3], BLACK)
        self.assertEqual(game.current_player, WHITE)
        self.assertEqual(agent.calls, 1)
        self.assertGreaterEqual(agent.llm_latency_seconds, 0)

    def test_agent_compatibility_check_does_not_change_game_state(self):
        game = Othello()
        original_board = game.get_board_state()
        original_history = list(game.history)
        model = FakeChatModel(MoveDecision(row=2, col=3, reason="Jogada legal."))
        agent = GroqAgent(llm=model)

        decision = agent.choose_move(game)

        self.assertEqual((decision.row, decision.col), (2, 3))
        self.assertEqual(game.get_board_state(), original_board)
        self.assertEqual(game.history, original_history)
        self.assertEqual(agent.calls, 1)

    def test_langgraph_agent_rejects_illegal_decision_without_mutation(self):
        game = Othello()
        original = game.get_board_state()
        model = FakeChatModel(MoveDecision(row=0, col=0, reason="Jogada inválida."))
        agent = GroqAgent(llm=model)

        with self.assertRaisesRegex(ValueError, "não é uma jogada legal"):
            agent.play_turn(game)

        self.assertEqual(game.get_board_state(), original)
        self.assertEqual(agent.calls, 1)


if __name__ == "__main__":
    unittest.main()
