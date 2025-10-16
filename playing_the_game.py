from __future__ import annotations
import time
from typing import Optional

from game_board import GameBoard, Move
from search_tool_box import SearchToolBox
from game_utilities import CumulativeAnalytics, PrettyAnalytics, MoveAnalytics

class PlayingTheGame:
    """
    Text UI loop for Human (White) vs Bot (Black).
    Complies with naming constraints for StartingMoveLocation and TargetingMoveLocation inputs.
    """
    def __init__(self, mode: str = "alpha-beta-ordering", seconds_budget: int = 2, ply_limit: int = 7):
        """
        Initialize a Checkers game with a specific search strategy and limits.

        mode:
        "minimax"               — plain minimax (no pruning)
        "alpha-beta"            — minimax with alpha-beta pruning
        "alpha-beta-ordering"   — alpha-beta pruning with node ordering
        """
        from game_board import GameBoard
        from search_tool_box import SearchToolBox
        from game_utilities import CumulativeAnalytics

        self.mode = mode
        self.SecondsBudget = seconds_budget
        self.PlyLimit = ply_limit

        # Determine algorithm features
        self.UseOrdering = (mode == "alpha-beta-ordering")
        self.UseAlphaBeta = (mode in ("alpha-beta", "alpha-beta-ordering"))

        # Initialize board and bot
        self.Board = GameBoard()
        self.Bot = SearchToolBox(mode=mode)

        # Initialize analytics trackers
        self.WhiteStats = CumulativeAnalytics()
        self.BlackStats = CumulativeAnalytics()



    def InputMove(self) -> Optional[Move]:
        print(self.Board.Pretty())
        try:
            sx = int(input("StartingMoveLocation Row (0-7): "))
            sy = int(input("StartingMoveLocation Col (0-7): "))
            tx = int(input("TargetingMoveLocation Row (0-7): "))
            ty = int(input("TargetingMoveLocation Col (0-7): "))
        except Exception:
            print("Invalid input. Please enter integers 0..7.")
            return None
        legal = self.Board.AllLegalMoves('w')
        for m in legal:
            if m.StartingMoveLocation == (sx, sy) and m.TargetingMoveLocation == (tx, ty):
                return m
        print("Illegal move (note: captures are mandatory if available). Try again.")
        return None

    def HumanTurn(self) -> bool:
        begin = time.time()
        while True:
            mv = self.InputMove()
            if mv is None:
                continue
            self.Board.ApplyMove(mv)
            elapsed = int((time.time() - begin) * 1000)
            man = MoveAnalytics(ElapsedMs=elapsed)
            self.WhiteStats.Add(man)
            print(PrettyAnalytics(len(self.WhiteStats.PerMove), "Human(White)", man))
            return True

    def BotTurn(self) -> bool:
        mv = self.Bot.ChooseMove(self.Board, 'b', SecondsBudget=self.SecondsBudget, PlyLimit=self.PlyLimit)
        if mv is None:
            print("Bot has no legal moves.")
            return False
        self.Board.ApplyMove(mv)
        self.BlackStats.Add(self.Bot.Analytics)
        print(PrettyAnalytics(len(self.BlackStats.PerMove), "Bot(Black)", self.Bot.Analytics))
        return True

    def Play(self) -> None:
        move_no = 1
        while True:
            if self.Board.IsTerminal():
                break
            print(f"\n===== Move {move_no}: Human(White) =====")
            if not self.HumanTurn():
                break
            if self.Board.IsTerminal():
                break
            print(f"\n===== Move {move_no}: Bot(Black) =====")
            if not self.BotTurn():
                break
            move_no += 1

        print("\n===== Game Over =====")
        print(self.Board.Pretty())
        if not self.Board._HasPieces('w'):
            print("Winner: Bot (Black)")
        elif not self.Board._HasPieces('b'):
            print("Winner: Human (White)")
        else:
            wm = len(self.Board.AllLegalMoves('w'))
            bm = len(self.Board.AllLegalMoves('b'))
            if wm == 0 and bm > 0:
                print("Winner: Bot (Black) by immobilization")
            elif bm == 0 and wm > 0:
                print("Winner: Human (White) by immobilization")
            else:
                print("Draw/Unknown termination.")

        print("\n-- Per-move Analytics: --")
        for i, m in enumerate(self.WhiteStats.PerMove, 1):
            print(PrettyAnalytics(i, "Human(White)", m))
        for i, m in enumerate(self.BlackStats.PerMove, 1):
            print(PrettyAnalytics(i, "Bot(Black)", m))

        print("\n-- Cumulative Analytics --")
        print("White:", self.WhiteStats.Summary())
        print("Black:", self.BlackStats.Summary())

if __name__ == "__main__":
    print("Configure your Checkers AI:\n")

    # --- Choose search algorithm (S) ---
    print("Choose search algorithm (S):")
    print("1 - Minimax")
    print("2 - Alpha-Beta Pruning")
    print("3 - Alpha-Beta Pruning with Node Ordering")
    while True:
        try:
            s_choice = int(input("Enter choice (1-3): "))
            if s_choice in (1, 2, 3):
                break
            print("Please enter 1, 2, or 3.")
        except ValueError:
            print("Invalid input. Try again.")

    if s_choice == 1:
        mode = "minimax"
    elif s_choice == 2:
        mode = "alpha-beta"
    else:
        mode = "alpha-beta-ordering"

    # --- Choose time limit (T) ---
    while True:
        try:
            T = int(input("Enter time limit T (1–3 seconds): "))
            if 1 <= T <= 3:
                break
            print("T must be between 1 and 3.")
        except ValueError:
            print("Please enter a valid integer.")

    # --- Choose ply depth (P) ---
    while True:
        try:
            P = int(input("Enter search depth P (5–9 plies): "))
            if 5 <= P <= 9:
                break
            print("P must be between 5 and 9.")
        except ValueError:
            print("Please enter a valid integer.")

    # Initialize game with selected options
    use_ordering = (mode == "alpha-beta-ordering")
    game = PlayingTheGame(mode=mode, seconds_budget=T, ply_limit=P)

    # Replace the default bot with the selected mode
    from search_tool_box import SearchToolBox
    game.Bot = SearchToolBox(mode=mode)

    game.Play()
