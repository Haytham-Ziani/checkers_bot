from __future__ import annotations
from typing import Optional, List, Tuple
import time

from game_board import GameBoard, Move
from game_utilities import MoveAnalytics, HeuristicScore

class SearchToolBox:
    """
    Provides Minimax with Alpha-Beta Pruning, with optional move ordering and
    time/ply limits.
    """
    def __init__(self, mode: str = "alpha-beta-ordering"):
        """
        mode:
        "minimax"               — plain minimax (no pruning)
        "alpha-beta"            — minimax with alpha-beta pruning
        "alpha-beta-ordering"   — alpha-beta pruning with move ordering
        """
        self.mode = mode
        self.UseOrdering = (mode == "alpha-beta-ordering")
        self.UseAlphaBeta = (mode in ("alpha-beta", "alpha-beta-ordering"))
        self.Analytics = MoveAnalytics()


    def ChooseMove(self, board: GameBoard, side: str, SecondsBudget: int = 2, PlyLimit: int = 7) -> Move:
        """Iterative deepening up to PlyLimit or SecondsBudget seconds.
        side: 'b' for bot, 'w' for human (if you ever make the bot play white).
        Returns the best Move for 'side'.
        """
        self.Analytics = MoveAnalytics()
        deadline = time.time() + max(1, SecondsBudget)

        best_move: Optional[Move] = None
        best_score = None
        # iterative deepening
        for depth in range(1, max(1, PlyLimit) + 1):
            move, score = self._SearchDepth(board, side, depth, deadline)
            if time.time() > deadline:
                break
            if move is not None:
                best_move, best_score = move, score
        if best_move is None:
            moves = board.AllLegalMoves(side)
            return moves[0] if moves else None
        return best_move

    def _OrderMoves(self, board: GameBoard, side: str, moves: List[Move]) -> List[Move]:
        if not self.UseOrdering:
            return moves
        scored = []
        for m in moves:
            clone = board.Clone()
            clone.ApplyMove(m)
            score = HeuristicScore(clone)
            if side == 'w':
                score = -score
            scored.append((score, m))
        scored.sort(key=lambda x: x[0], reverse=True)
        self.Analytics.OrderingComparisons += max(0, len(scored) - 1)
        return [m for _, m in scored]

    def _SearchDepth(self, board: GameBoard, side: str, depth: int, deadline: float) -> Tuple[Optional[Move], Optional[int]]:
        start = time.time()
        maximizing = (side == 'b')
        best_move = None
        alpha, beta = -10**9, 10**9

        def max_value(bd: GameBoard, d: int, a: int, be: int) -> int:
            if time.time() > deadline:
                return HeuristicScore(bd)
            self.Analytics.NodesExpanded += 1
            if d == 0 or bd.IsTerminal():
                return HeuristicScore(bd)
            moves = bd.AllLegalMoves('b')
            if not moves:
                return HeuristicScore(bd)
            ordered = self._OrderMoves(bd, 'b', moves)
            best = -10**9
            for m in ordered:
                clone = bd.Clone()
                clone.ApplyMove(m)
                val = min_value(clone, d-1, a, be)
                best = max(best, val)
                a = max(a, best)
                if self.UseAlphaBeta and a >= be:
                    self.Analytics.AlphaBetaCuts += 1
                    break
            return best

        def min_value(bd: GameBoard, d: int, a: int, be: int) -> int:
            if time.time() > deadline:
                return HeuristicScore(bd)
            self.Analytics.NodesExpanded += 1
            if d == 0 or bd.IsTerminal():
                return HeuristicScore(bd)
            moves = bd.AllLegalMoves('w')
            if not moves:
                return HeuristicScore(bd)
            ordered = self._OrderMoves(bd, 'w', moves)
            best = 10**9
            for m in ordered:
                clone = bd.Clone()
                clone.ApplyMove(m)
                val = max_value(clone, d-1, a, be)
                best = min(best, val)
                be = min(be, best)
                if self.UseAlphaBeta and a >= be:
                    self.Analytics.AlphaBetaCuts += 1
                    break
            return best

        moves = board.AllLegalMoves(side)
        if not moves:
            return None, None
        moves = self._OrderMoves(board, side, moves)
        best_score = -10**9 if maximizing else 10**9
        for idx, m in enumerate(moves):
            clone = board.Clone()
            clone.ApplyMove(m)
            if maximizing:
                score = min_value(clone, depth-1, alpha, beta)
                if score > best_score:
                    if idx > 0:
                        self.Analytics.OrderingGains += 1
                    best_score, best_move = score, m
                alpha = max(alpha, best_score)
            else:
                score = max_value(clone, depth-1, alpha, beta)
                if score < best_score:
                    if idx > 0:
                        self.Analytics.OrderingGains += 1
                    best_score, best_move = score, m
                beta = min(beta, best_score)
            if time.time() > deadline:
                break

        self.Analytics.ElapsedMs += int((time.time() - start) * 1000)
        return best_move, best_score
