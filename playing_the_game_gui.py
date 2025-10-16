from __future__ import annotations
import tkinter as tk
from tkinter import messagebox
import time

from game_board import GameBoard, Move
from search_tool_box import SearchToolBox
from game_utilities import CumulativeAnalytics, PrettyAnalytics, MoveAnalytics

BOARD_SIZE = 8
SQUARE = 80
PADDING = 30
WINDOW_W = SQUARE * BOARD_SIZE + PADDING * 2
WINDOW_H = SQUARE * BOARD_SIZE + PADDING * 2 + 50  # room for status

DARK = "#6b4f3a"
LIGHT = "#f0d9b5"
HIGHLIGHT = "#8fd3ff"
PIECE_WHITE = "#eeeeee"
PIECE_BLACK = "#222222"
KING_RING = "#ffd700"

class TkCheckersApp:
    """
    Tkinter UI that reuses the same four core classes.
    Analytics remain printed to the console per the user's preference.
    """
    def __init__(self, root, seconds_budget=2, ply_limit=7, use_ordering=True):
        assert 1 <= seconds_budget <= 3, "T must be 1..3 seconds"
        assert 5 <= ply_limit <= 9, "P must be 5..9 plies"

        self.root = root
        root.title("CSC-3309 Checkers (Human=White, Bot=Black)")
        root.resizable(False, False)

        self.canvas = tk.Canvas(root, width=WINDOW_W, height=WINDOW_H, highlightthickness=0)
        self.canvas.pack()

        # --- Buttons for New Game / Exit ---
        button_frame = tk.Frame(root)
        button_frame.pack(pady=5)

        btn_new = tk.Button(button_frame, text="New Game", command=self.NewGame, width=12)
        btn_new.grid(row=0, column=0, padx=10)

        btn_exit = tk.Button(button_frame, text="Exit", command=root.destroy, width=12)
        btn_exit.grid(row=0, column=1, padx=10)


        self.Board = GameBoard()
        self.Bot = SearchToolBox(mode=("alpha-beta-ordering" if use_ordering else "alpha-beta"))
        self.SecondsBudget = seconds_budget
        self.PlyLimit = ply_limit
        self.WhiteStats = CumulativeAnalytics()
        self.BlackStats = CumulativeAnalytics()

        self.Selected = None  # (r,c) or None
        self.LegalTargets = []  # list of moves for selected piece
        self.Status = tk.StringVar()
        self.Status.set("Your turn: click a white piece, then a destination square.")
        self.canvas.bind("<Button-1>", self.OnClick)

        self.DrawBoard()

    def DrawBoard(self):
        self.canvas.delete("all")
        # squares
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                x0 = PADDING + c * SQUARE
                y0 = PADDING + r * SQUARE
                x1 = x0 + SQUARE
                y1 = y0 + SQUARE
                color = DARK if (r + c) % 2 else LIGHT
                self.canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="")

        # selection & targets
        if self.Selected is not None:
            sr, sc = self.Selected
            self._HighlightSquare(sr, sc, HIGHLIGHT)
            for mv in self.LegalTargets:
                tr, tc = mv.TargetingMoveLocation
                self._HighlightSquare(tr, tc, HIGHLIGHT)

        # pieces
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                p = self.Board.board[r][c]
                if p == '.':
                    continue
                x0 = PADDING + c * SQUARE + 8
                y0 = PADDING + r * SQUARE + 8
                x1 = x0 + SQUARE - 16
                y1 = y0 + SQUARE - 16
                fill = PIECE_WHITE if p.lower() == 'w' else PIECE_BLACK
                self.canvas.create_oval(x0, y0, x1, y1, fill=fill, outline="black", width=2)
                if p.isupper():
                    self.canvas.create_oval(x0+10, y0+10, x1-10, y1-10, outline=KING_RING, width=4)

        self.canvas.create_text(WINDOW_W//2, WINDOW_H - 20, text=self.Status.get(), font=("Arial", 12))

    def _HighlightSquare(self, r, c, color):
        x0 = PADDING + c * SQUARE
        y0 = PADDING + r * SQUARE
        x1 = x0 + SQUARE
        y1 = y0 + SQUARE
        self.canvas.create_rectangle(x0, y0, x1, y1, outline=color, width=4)

    def OnClick(self, event):
        if self.Board.IsTerminal():
            return

        r, c = self._PixelToSquare(event.x, event.y)
        if r is None:
            return

        current_legal = self.Board.AllLegalMoves('w')

        if self.Selected is None:
            if self.Board.PieceAt((r,c)) not in ('w','W'):
                return
            self.LegalTargets = [m for m in current_legal if m.StartingMoveLocation == (r,c)]
            if not self.LegalTargets:
                return
            self.Selected = (r, c)
            self.Status.set("Select a destination square.")
            self.DrawBoard()
            return

        chosen = None
        for mv in self.LegalTargets:
            if mv.TargetingMoveLocation == (r,c):
                chosen = mv
                break

        if chosen is None:
            if self.Board.PieceAt((r,c)) in ('w','W'):
                self.Selected = None
                self.LegalTargets = []
                self.OnClick(event)
            return

        # Human move
        self.Board.ApplyMove(chosen)
        man = MoveAnalytics(ElapsedMs=0)
        self.WhiteStats.Add(man)
        print(PrettyAnalytics(len(self.WhiteStats.PerMove), "Human(White)", man))

        self.Selected = None
        self.LegalTargets = []
        self.Status.set("Bot is thinking...")
        self.DrawBoard()
        self.root.update_idletasks()
        self.root.after(50, self.BotTurn)

    def BotTurn(self):
        if self.Board.IsTerminal():
            self.GameOver()
            return
        mv = self.Bot.ChooseMove(self.Board, 'b', SecondsBudget=self.SecondsBudget, PlyLimit=self.PlyLimit)
        if mv is None:
            self.Status.set("Bot has no legal moves.")
            self.DrawBoard()
            self.GameOver()
            return
        self.Board.ApplyMove(mv)
        self.BlackStats.Add(self.Bot.Analytics)
        print(PrettyAnalytics(len(self.BlackStats.PerMove), "Bot(Black)", self.Bot.Analytics))

        if self.Board.IsTerminal():
            self.DrawBoard()
            self.GameOver()
            return

        self.Status.set("Your turn: click a white piece, then a destination square.")
        self.DrawBoard()

    def NewGame(self):
        if not self.Board.IsTerminal():
            if not messagebox.askyesno("Confirm", "A game is in progress. Start a new game?"):
                return
        self.Board = GameBoard()
        self.WhiteStats = CumulativeAnalytics()
        self.BlackStats = CumulativeAnalytics()
        self.Selected = None
        self.LegalTargets = []
        self.Status.set("Your turn: click a white piece, then a destination square.")
        self.DrawBoard()

    def GameOver(self):
        msg = ["Game Over."]
        if not self.Board._HasPieces('w'):
            msg.append("Winner: Bot (Black)")
        elif not self.Board._HasPieces('b'):
            msg.append("Winner: Human (White)")
        else:
            wm = len(self.Board.AllLegalMoves('w'))
            bm = len(self.Board.AllLegalMoves('b'))
            if wm == 0 and bm > 0:
                msg.append("Winner: Bot (Black) by immobilization")
            elif bm == 0 and wm > 0:
                msg.append("Winner: Human (White) by immobilization")
            else:
                msg.append("Draw/Unknown termination.")

        print("\n-- Per-move Analytics: --")
        for i, m in enumerate(self.WhiteStats.PerMove, 1):
            print(PrettyAnalytics(i, "Human(White)", m))
        for i, m in enumerate(self.BlackStats.PerMove, 1):
            print(PrettyAnalytics(i, "Bot(Black)", m))

        print("\n-- Cumulative Analytics --")
        print("White:", self.WhiteStats.Summary())
        print("Black:", self.BlackStats.Summary())

        messagebox.showinfo("Game Over", "\n".join(msg))

    def _PixelToSquare(self, x, y):
        if not (PADDING <= x <= PADDING + BOARD_SIZE * SQUARE and PADDING <= y <= PADDING + BOARD_SIZE * SQUARE):
            return None, None
        c = (x - PADDING) // SQUARE
        r = (y - PADDING) // SQUARE
        return int(r), int(c)

def main():
    print("Configure your Checkers AI:")

    # --- Select algorithm S ---
    print("\nChoose search algorithm (S):")
    print("1 - Minimax")
    print("2 - Alpha-Beta Pruning")
    print("3 - Alpha-Beta Pruning with Node Ordering")
    while True:
        try:
            choice = int(input("Enter choice (1-3): "))
            if choice in (1, 2, 3):
                break
            print("Please enter 1, 2, or 3.")
        except ValueError:
            print("Invalid input. Try again.")

    if choice == 1:
        mode = "minimax"
    elif choice == 2:
        mode = "alpha-beta"
    else:
        mode = "alpha-beta-ordering"

    # --- Select time limit (T) ---
    while True:
        try:
            T = int(input("Enter time limit T (1–3 seconds): "))
            if 1 <= T <= 3:
                break
            print("T must be between 1 and 3.")
        except ValueError:
            print("Please enter a valid integer.")

    # --- Select ply depth (P) ---
    while True:
        try:
            P = int(input("Enter search depth P (5–9 plies): "))
            if 5 <= P <= 9:
                break
            print("P must be between 5 and 9.")
        except ValueError:
            print("Please enter a valid integer.")

    root = tk.Tk()
    app = TkCheckersApp(root, seconds_budget=T, ply_limit=P, use_ordering=(mode == "alpha-beta-ordering"))
    # Override bot with chosen mode
    app.Bot = SearchToolBox(mode=mode)
    app.DrawBoard()
    root.mainloop()


if __name__ == "__main__":
    main()
