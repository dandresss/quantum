import pytest

from quantum_app.maze import generate


def test_bot_plays_progressive_attempts(client):
    grid = generate("binary_tree", 4, 3, 0.2, seed=2)
    resp = client.post("/api/bot/play", json={"grid": grid})
    assert resp.status_code == 200
    body = resp.json()
    assert body["tick_ms"] > 0
    attempts = body["attempts"]
    assert [a["trained"] for a in attempts] == [0.1, 0.3, 0.6, 1.0]
    for attempt in attempts:
        path = attempt["path"]
        assert path[0] == [1, 1]
        assert attempt["steps"] == len(path) - 1
        for (r1, c1), (r2, c2) in zip(path, path[1:], strict=False):
            assert abs(r1 - r2) + abs(c1 - c2) <= 1  # moves one cell or bumps a wall
            assert grid[r2][c2] == 0
        assert attempt["reached"] == (path[-1] == [len(grid) - 2, len(grid[0]) - 2])
    assert attempts[-1]["reached"]  # fully trained bot escapes this small maze


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


def test_random_moves_always_go_to_a_free_cell():
    from agent import QAgent

    grid = generate("backtracker", 5, 4, 0.2, seed=3)
    agent = QAgent(grid, (1, 1), (7, 9), seed=0)
    path, _ = agent.rollout(agent.Q, eps=1.0, max_steps=300)  # every move is random
    assert all(a != b for a, b in zip(path, path[1:], strict=False))  # never bumps a wall


def test_bot_obeys_q_85_percent_of_moves():
    from bot import LEVELS

    assert all(level["eps"] == 0.15 for level in LEVELS.values())


def test_race_uses_the_q_table_at_80_percent(client):
    grid = generate("binary_tree", 4, 3, 0.2, seed=2)
    race = client.post("/api/bot/play", json={"grid": grid}).json()["race"]
    assert race["trained"] == 0.8
    assert race["path"][0] == [1, 1] and race["steps"] == len(race["path"]) - 1
    assert all(grid[r][c] == 0 for r, c in race["path"])
