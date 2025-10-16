from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, List

from game_board import GameBoard

@dataclass
class MoveAnalytics:
    NodesExpanded: int = 0
    MaxFringeSize: int = 0
    AlphaBetaCuts: int = 0
    OrderingComparisons: int = 0
    OrderingGains: int = 0  # Count of times a better move was found earlier due to ordering
    ElapsedMs: int = 0

@dataclass
class CumulativeAnalytics:
    PerMove: List[MoveAnalytics] = field(default_factory=list)

    def Add(self, m: MoveAnalytics) -> None:
        self.PerMove.append(m)

    def Summary(self) -> Dict[str, Any]:
        total = MoveAnalytics()
        for m in self.PerMove:
            total.NodesExpanded += m.NodesExpanded
            total.MaxFringeSize = max(total.MaxFringeSize, m.MaxFringeSize)
            total.AlphaBetaCuts += m.AlphaBetaCuts
            total.OrderingComparisons += m.OrderingComparisons
            total.OrderingGains += m.OrderingGains
            total.ElapsedMs += m.ElapsedMs
        return {
            "TotalNodesExpanded": total.NodesExpanded,
            "MaxFringeSize": total.MaxFringeSize,
            "TotalAlphaBetaCuts": total.AlphaBetaCuts,
            "TotalOrderingComparisons": total.OrderingComparisons,
            "TotalOrderingGains": total.OrderingGains,
            "TotalElapsedMs": total.ElapsedMs
        }

def PrettyAnalytics(move_index: int, who: str, m: MoveAnalytics) -> str:
    return (
        f"[Move {move_index} - {who}] "
        f"NodesExpanded={m.NodesExpanded}, MaxFringeSize={m.MaxFringeSize}, "
        f"AlphaBetaCuts={m.AlphaBetaCuts}, OrderingComparisons={m.OrderingComparisons}, "
        f"OrderingGains={m.OrderingGains}, ElapsedMs={m.ElapsedMs}"
    )

def HeuristicScore(board: GameBoard) -> int:
    """Simple but strong heuristic evaluating material and advancement.
    Positive is good for black (bot), negative for white (human).
    """
    value = 0
    for r in range(board.size):
        for c in range(board.size):
            p = board.board[r][c]
            if p == 'b':
                value += 3 + r  # reward advancing
            elif p == 'B':
                value += 5
            elif p == 'w':
                value -= 3 + (board.size - 1 - r)
            elif p == 'W':
                value -= 5
    return value
