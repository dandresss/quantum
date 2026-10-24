import pytest

from quantum_app.maze import generate


def test_bot_plays_a_valid_path(client):
    grid = generate("binary_tree", 4, 3, 0.2, seed=2)
    resp = client.post("/api/bot/play", json={"grid": grid})
    assert resp.status_code == 200
    body = resp.json()
    path = body["path"]
    assert path[0] == [1, 1]
    assert body["steps"] == len(path) - 1 and body["tick_ms"] > 0
    for (r1, c1), (r2, c2) in zip(path, path[1:], strict=False):
        assert abs(r1 - r2) + abs(c1 - c2) <= 1  # moves one cell or bumps a wall
        assert grid[r2][c2] == 0
    assert body["reached"] == (path[-1] == [len(grid) - 2, len(grid[0]) - 2])


@pytest.mark.parametrize(
    "grid",
    [
        generate("binary_tree", 16, 5, 0.2, seed=1),  # wider than 15 cells
        [[1, 1, 1], [1, 0, 1]],  # too small
        [[1, 1, 1, 1], [1, 0, 1], [1, 1, 1, 1]],  # ragged
        [[1, 1, 1, 1, 1], [1, 0, 1, 0, 1], [1, 1, 1, 1, 1]],  # no path to goal
        [[1, 2, 1], [1, 0, 1], [1, 1, 1]],  # not 0/1
    ],
)
def test_bot_rejects_invalid_grids(client, grid):
    assert client.post("/api/bot/play", json={"grid": grid}).status_code == 422
