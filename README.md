# Checkers Agent (CSC-3309 Mini Project 2)

A modern, AI-powered Checkers game with both GUI and text-based interfaces. Play against an intelligent agent using Minimax, Minimax with Alpha Beta pruning, or Alpha-Beta with move ordering.

## Run (Text UI)
```bash
python playing_the_game.py
```

## Run (Tkinter GUI)
```bash
python playing_the_game_gui.py
```
- Click a white piece, then a highlighted destination.
- Bot responds within the configured time/depth.
- **Analytics are printed to the console**.

## Configure S/T/P
- `SecondsBudget` ∈ {1,2,3}
- `PlyLimit` ∈ {5,6,7,8,9}
- `UseOrdering`: True/False

## Requirements
- Python 3.x
- Tkinter (for GUI; pre-installed on most systems)

## Files
- `game_board.py` — Board state, legal move generation (forced capture, multi-jump, kinging), apply move.
- `search_tool_box.py` — Minimax + Alpha-Beta, move ordering, iterative deepening, analytics.
- `playing_the_game.py` — Text interface, analytics printouts.
- `playing_the_game_gui.py` — Tkinter GUI that prints analytics to console.
- `game_utilities.py` — Heuristic + analytics data classes.
