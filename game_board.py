from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple

Coordinate = Tuple[int, int]
@dataclass
class Move:
    # Single checker move from a StartingMoveLocation to a TargetingMoveLocation.
    StartingMoveLocation: Coordinate
    TargetingMoveLocation: Coordinate
    path: List[Coordinate]
    is_capture: bool
    captured: List[Coordinate]

class GameBoard:
    """
    8x8 Checkers board with the following piece encoding: 'w' = white man (human), 'W' = white king; 'b' = black man (bot),   'B' = black king; '.' = empty
    White moves 'up' (towards decreasing rows); Black moves 'down' (towards increasing rows). Capture is mandatory when available.
    """
    def __init__(self) -> None:
        self.size = 8
        self.board = self._InitialBoard()

    def _InitialBoard(self) -> List[List[str]]:
        b = [['.' for _ in range(self.size)] for _ in range(self.size)]

        for r in range(3):
            for c in range(self.size):
                if (r + c) % 2 == 1: # dark square
                    b[r][c] = 'b'
        for r in range(5, 8):
            for c in range(self.size):
                if (r + c) % 2 == 1:
                    b[r][c] = 'w'
        return b

    def Clone(self) -> 'GameBoard': 
        g = GameBoard()
        g.board = [row[:] for row in self.board]
        return g

    def Inside(self, r: int, c: int) -> bool: # is (r,c) on the board?
        return 0 <= r < self.size and 0 <= c < self.size

    def PieceAt(self, rc: Coordinate) -> str: # return piece at (r,c)
        r, c = rc
        return self.board[r][c]

    def SetPiece(self, rc: Coordinate, piece: str) -> None: # place/replace piece at (r,c)
        r, c = rc
        self.board[r][c] = piece

    def IsTerminal(self) -> bool: # game over? either side has no pieces or no legal moves
        return (not self._HasPieces('w') or not self._HasPieces('b') or
                (len(self.AllLegalMoves('w')) == 0) or (len(self.AllLegalMoves('b')) == 0))

    def _HasPieces(self, side: str) -> bool: # does side ('w' or 'b') have any pieces left?
        targets = ('w', 'W') if side == 'w' else ('b', 'B')
        return any(cell in targets for row in self.board for cell in row)

    def _Directions(self, piece: str): # movement directions for piece
        if piece in ('w', 'W'):
            ups = [(-1, -1), (-1, 1)]
            if piece == 'W':  # king
                return ups + [(1, -1), (1, 1)]
            return ups
        else:
            downs = [(1, -1), (1, 1)]
            if piece == 'B':  # king
                return downs + [(-1, -1), (1, 1)]
            return downs

    def _Opponents(self, side: str): 
        return ('b', 'B') if side == 'w' else ('w', 'W')

    def AllLegalMoves(self, side: str) -> List[Move]:
        """Return all legal moves for side ('w' or 'b') honoring mandatory capture."""
        captures = []
        quiets = []
        for r in range(self.size):
            for c in range(self.size):
                piece = self.board[r][c]
                if piece == '.':
                    continue
                if side == 'w' and piece not in ('w', 'W'):
                    continue
                if side == 'b' and piece not in ('b', 'B'):
                    continue
                caps, qs = self._MovesFrom((r, c), piece, side)
                captures.extend(caps)
                quiets.extend(qs)
        return captures if captures else quiets

    def _MovesFrom(self, rc: Coordinate, piece: str, side: str):
        """Return (captures, quiets) from a given square, including multi-jumps for captures."""
        captures = []
        quiets = []
        seen = set()

        def try_quiet(fr: int, fc: int, dr: int, dc: int):
            nr, nc = fr + dr, fc + dc
            if self.Inside(nr, nc) and self.board[nr][nc] == '.':
                mv = Move(StartingMoveLocation=(fr, fc),
                          TargetingMoveLocation=(nr, nc),
                          path=[(fr, fc), (nr, nc)],
                          is_capture=False,
                          captured=[])
                quiets.append(mv)

        def try_captures(fr: int, fc: int, piece_local: str, path, captured): # recursive multi-jump
            found = False
            for dr, dc in self._Directions(piece_local):
                mr, mc = fr + dr, fc + dc
                lr, lc = fr + 2*dr, fc + 2*dc
                if (self.Inside(lr, lc) and self.board[lr][lc] == '.' and
                        self.Inside(mr, mc) and self.board[mr][mc] in self._Opponents(side)):
                    cap_pos = (mr, mc)
                    if cap_pos in captured:
                        continue
                    orig = self.board[fr][fc]
                    self.board[fr][fc] = '.'
                    cap_orig = self.board[mr][mc]
                    self.board[mr][mc] = '.'
                    landed_piece = piece_local
                    if side == 'w' and lr == 0 and piece_local == 'w':
                        landed_piece = 'W'
                    if side == 'b' and lr == self.size - 1 and piece_local == 'b':
                        landed_piece = 'B'
                    dest_orig = self.board[lr][lc]
                    self.board[lr][lc] = landed_piece
                    try:
                        found = True
                        try_captures(lr, lc, landed_piece, path + [(lr, lc)], captured + [cap_pos])
                    finally:
                        self.board[fr][fc] = orig
                        self.board[mr][mc] = cap_orig
                        self.board[lr][lc] = dest_orig
            if not found and len(captured) > 0:
                mv = Move(StartingMoveLocation=path[0],
                          TargetingMoveLocation=path[-1],
                          path=path[:],
                          is_capture=True,
                          captured=captured[:])
                key = (mv.StartingMoveLocation, tuple(mv.path), tuple(mv.captured))
                if key not in seen:
                    captures.append(mv)
                    seen.add(key)

        r, c = rc
        # Generate quiets
        for dr, dc in self._Directions(piece):
            try_quiet(r, c, dr, dc)

        # Generate captures
        try_captures(r, c, piece, [(r, c)], [])

        return captures, quiets

    def ApplyMove(self, move: Move) -> None:
        sr, sc = move.StartingMoveLocation
        tr, tc = move.TargetingMoveLocation
        piece = self.board[sr][sc]
        self.board[sr][sc] = '.'
        for cr, cc in move.captured:
            self.board[cr][cc] = '.'
        if piece == 'w' and tr == 0:
            piece = 'W'
        elif piece == 'b' and tr == self.size - 1:
            piece = 'B'
        self.board[tr][tc] = piece

    def Pretty(self) -> str:
        lines = []
        header = "   " + " ".join(str(c) for c in range(self.size))
        lines.append(header)
        for r in range(self.size):
            line = [str(r)]
            for c in range(self.size):
                line.append(self.board[r][c])
            lines.append(f"{r}  " + " ".join(line[1:]))
        return "\n".join(lines)
