"""Maze generation on a (2*height+1) x (2*width+1) grid where 1 is wall and 0 is path.

Cell (x, y) lives at grid[2*y+1][2*x+1]; the grid squares between cells are walls
that algorithms carve open. `braid` (0-1) adds loops: higher means easier.
"""

import random

WALL, PATH = 1, 0


def binary_tree(width: int, height: int, braid: float, rng: random.Random) -> list[list[int]]:
    """Each cell carves north or west; with probability `braid` it carves both."""
    grid = [[WALL] * (2 * width + 1) for _ in range(2 * height + 1)]
    for y in range(height):
        for x in range(width):
            r, c = 2 * y + 1, 2 * x + 1
            grid[r][c] = PATH
            options = []
            if y > 0:
                options.append((r - 1, c))
            if x > 0:
                options.append((r, c - 1))
            if len(options) == 2 and rng.random() < braid:
                for wr, wc in options:
                    grid[wr][wc] = PATH
            elif options:
                wr, wc = rng.choice(options)
                grid[wr][wc] = PATH
    return grid


def backtracker(width: int, height: int, braid: float, rng: random.Random) -> list[list[int]]:
    """Depth-first carving (long winding corridors); `braid` opens dead ends."""
    grid = [[WALL] * (2 * width + 1) for _ in range(2 * height + 1)]
    grid[1][1] = PATH
    stack, visited = [(0, 0)], {(0, 0)}
    while stack:
        x, y = stack[-1]
        unvisited = [n for n in _neighbors(x, y, width, height) if n not in visited]
        if not unvisited:
            stack.pop()
            continue
        nx, ny = rng.choice(unvisited)
        grid[y + ny + 1][x + nx + 1] = PATH
        grid[2 * ny + 1][2 * nx + 1] = PATH
        visited.add((nx, ny))
        stack.append((nx, ny))

    for y in range(height):
        for x in range(width):
            neighbors = _neighbors(x, y, width, height)
            closed = [(nx, ny) for nx, ny in neighbors if grid[y + ny + 1][x + nx + 1] == WALL]
            if len(neighbors) - len(closed) == 1 and rng.random() < braid:
                nx, ny = rng.choice(closed)
                grid[y + ny + 1][x + nx + 1] = PATH
    return grid


def _neighbors(x: int, y: int, width: int, height: int) -> list[tuple[int, int]]:
    candidates = [(x, y - 1), (x + 1, y), (x, y + 1), (x - 1, y)]
    return [(nx, ny) for nx, ny in candidates if 0 <= nx < width and 0 <= ny < height]


ALGORITHMS = {"binary_tree": binary_tree, "backtracker": backtracker}


def generate(
    algorithm: str, width: int, height: int, braid: float = 0.2, seed: int | None = None
) -> list[list[int]]:
    if width < 1 or height < 1:
        raise ValueError("width and height must be at least 1")
    if not 0.0 <= braid <= 1.0:
        raise ValueError("braid must be between 0 and 1")
    if algorithm not in ALGORITHMS:
        raise ValueError(f"unknown algorithm {algorithm!r}")
    return ALGORITHMS[algorithm](width, height, braid, random.Random(seed))
