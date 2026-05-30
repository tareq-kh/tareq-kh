# Tetris

A classic falling-blocks game written in Python with [pygame](https://www.pygame.org/).

![Python](https://img.shields.io/badge/python-3.8+-blue)

## Features

- Standard 10×20 playfield with the seven classic tetrominoes
- **7-bag randomizer** so piece distribution feels fair
- **Ghost piece** showing where the current piece will land
- **Hold** queue and **next piece** preview
- **Wall kicks** on rotation
- Soft drop, hard drop, scoring, line clears, and increasing levels/speed
- Pause and restart

## Install

```bash
pip install -r requirements.txt
```

## Play

```bash
python tetris.py
```

## Controls

| Key            | Action                       |
| -------------- | ---------------------------- |
| ← / →          | Move left / right            |
| ↓              | Soft drop                    |
| ↑ or **X**     | Rotate clockwise             |
| **Z**          | Rotate counter-clockwise     |
| **Space**      | Hard drop                    |
| **C**          | Hold piece                   |
| **P**          | Pause / resume               |
| **Esc** / **Q**| Quit                         |
| **R**          | Restart (after game over)    |

## Scoring

| Lines cleared | Base points |
| ------------- | ----------- |
| 1 (single)    | 100         |
| 2 (double)    | 300         |
| 3 (triple)    | 500         |
| 4 (tetris)    | 800         |

Points are multiplied by the current level, and a hard drop awards 2 points per
cell dropped. You advance one level for every 10 lines cleared, and each level
makes the pieces fall faster.
