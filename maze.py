"""Maze generation via iterative recursive backtracking (randomized DFS).

Run manually to print a maze: `uv run python maze.py --width 20 --height 10`
"""

import argparse
import random

WALL = 1
PATH = 0

DIRECTIONS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def generate(
    width: int,
    height: int,
    braid: float = 0.0,
    seed: int | None = None,
) -> list[list[int]]:
    """Return a (2*height+1) x (2*width+1) grid where 1 is wall and 0 is path.

    Cells live at odd coordinates; the even ones in between are walls that get
    carved. `braid` is the probability of opening each remaining inner wall,
    which adds loops and makes the maze easier.
    """
    if width < 1 or height < 1:
        raise ValueError("width and height must be at least 1")
    if not 0.0 <= braid <= 1.0:
        raise ValueError("braid must be between 0 and 1")

    rng = random.Random(seed)
    rows, cols = 2 * height + 1, 2 * width + 1
    grid = [[WALL] * cols for _ in range(rows)]

    start = (0, 0)
    grid[1][1] = PATH
    visited = {start}
    stack = [start]

    while stack:
        x, y = stack[-1]
        neighbors = [
            (x + dx, y + dy)
            for dx, dy in DIRECTIONS
            if 0 <= x + dx < width and 0 <= y + dy < height and (x + dx, y + dy) not in visited
        ]
        if not neighbors:
            stack.pop()
            continue
        nx, ny = rng.choice(neighbors)
        grid[y + ny + 1][x + nx + 1] = PATH
        grid[2 * ny + 1][2 * nx + 1] = PATH
        visited.add((nx, ny))
        stack.append((nx, ny))

    if braid:
        for r in range(1, rows - 1):
            for c in range(1, cols - 1):
                # Wall between two cells: exactly one coordinate is even.
                if grid[r][c] == WALL and (r + c) % 2 == 1 and rng.random() < braid:
                    grid[r][c] = PATH

    return grid


def render(grid: list[list[int]]) -> str:
    rows, cols = len(grid), len(grid[0])
    start, end = (1, 1), (rows - 2, cols - 2)
    lines = []
    for r in range(rows):
        line = []
        for c in range(cols):
            if (r, c) == start:
                line.append("S ")
            elif (r, c) == end:
                line.append("E ")
            else:
                line.append("██" if grid[r][c] == WALL else "  ")
        lines.append("".join(line))
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Print a randomly generated maze.")
    parser.add_argument("--width", type=int, default=15, help="cells per row")
    parser.add_argument("--height", type=int, default=10, help="cells per column")
    parser.add_argument("--braid", type=float, default=0.0, help="0-1, extra openings")
    parser.add_argument("--seed", type=int, default=None, help="for reproducible mazes")
    args = parser.parse_args()

    grid = generate(args.width, args.height, braid=args.braid, seed=args.seed)
    print(render(grid))


if __name__ == "__main__":
    main()
