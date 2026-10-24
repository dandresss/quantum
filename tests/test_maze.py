import pytest

from quantum_app.maze import ALGORITHMS, PATH, WALL, generate


def reachable_cells(grid):
    seen, todo = {(1, 1)}, [(1, 1)]
    while todo:
        r, c = todo.pop()
        for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if grid[nr][nc] == PATH and (nr, nc) not in seen:
                seen.add((nr, nc))
                todo.append((nr, nc))
    return {(r, c) for r, c in seen if r % 2 and c % 2}


def open_passages(grid):
    return sum(v == PATH for row in grid for v in row) - sum(
        grid[r][c] == PATH for r in range(1, len(grid), 2) for c in range(1, len(grid[0]), 2)
    )


@pytest.mark.parametrize("algorithm", ALGORITHMS)
@pytest.mark.parametrize("braid", [0.0, 0.5, 1.0])
def test_shape_borders_and_connectivity(algorithm, braid):
    grid = generate(algorithm, 12, 7, braid, seed=1)
    assert len(grid) == 15 and all(len(row) == 25 for row in grid)
    assert all(
        v == WALL for v in grid[0] + grid[-1] + [row[0] for row in grid] + [row[-1] for row in grid]
    )
    assert len(reachable_cells(grid)) == 12 * 7


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_no_braid_is_a_perfect_maze(algorithm):
    # A spanning tree over w*h cells has exactly w*h - 1 passages (no loops).
    assert open_passages(generate(algorithm, 10, 10, 0.0, seed=3)) == 10 * 10 - 1


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_braid_adds_loops(algorithm):
    assert open_passages(generate(algorithm, 10, 10, 1.0, seed=3)) > 10 * 10 - 1


def test_seed_is_reproducible():
    assert generate("backtracker", 8, 8, 0.3, seed=9) == generate("backtracker", 8, 8, 0.3, seed=9)


@pytest.mark.parametrize(
    "args", [("binary_tree", 0, 5, 0.2), ("binary_tree", 5, 5, 1.5), ("prim", 5, 5, 0.2)]
)
def test_invalid_args(args):
    with pytest.raises(ValueError):
        generate(*args)


def test_maze_endpoint(client):
    resp = client.get("/api/maze", params={"algorithm": "backtracker", "width": 6, "height": 4})
    assert resp.status_code == 200
    grid = resp.json()["grid"]
    assert len(grid) == 9 and len(grid[0]) == 13


@pytest.mark.parametrize(
    "params", [{"algorithm": "prim"}, {"width": 1}, {"height": 51}, {"braid": 2}]
)
def test_maze_endpoint_validation(client, params):
    assert client.get("/api/maze", params=params).status_code == 422
