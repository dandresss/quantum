import pytest

from quantum_app.maze import generate


def shortest(grid):
    from collections import deque

    goal = (len(grid) - 2, len(grid[0]) - 2)
    dist, queue = {(1, 1): 0}, deque([(1, 1)])
    while queue:
        r, c = queue.popleft()
        for n in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if grid[n[0]][n[1]] == 0 and n not in dist:
                dist[n] = dist[(r, c)] + 1
                queue.append(n)
    return dist[goal]


def test_quantum_maze_endpoint(client):
    params = {"algorithm": "backtracker", "width": 6, "height": 4, "seed": 5, "quantum": True}
    grid = client.get("/api/maze", params=params).json()["grid"]
    assert len(grid) == 9 and len(grid[0]) == 13
    assert grid == client.get("/api/maze", params=params).json()["grid"]  # seed repeats it
    classic = client.get("/api/maze", params={**params, "quantum": False}).json()["grid"]
    assert grid != classic  # different source of randomness


def test_expert_quantum_bot_takes_the_shortest_path(client):
    grid = generate("backtracker", 8, 6, 0.2, seed=4)
    body = client.post("/api/bot/quantum", json={"grid": grid, "level": "expert"}).json()
    path = body["path"]
    assert body["reached"] and path[0] == [1, 1] and path[-1] == [len(grid) - 2, len(grid[0]) - 2]
    assert body["steps"] == len(path) - 1 == shortest(grid)
    assert body["tick_ms"] > 0 and body["queries"]["quantum"] == body["steps"]


def test_hard_quantum_bot_still_escapes(client):
    grid = generate("binary_tree", 8, 6, 0.2, seed=1)
    body = client.post("/api/bot/quantum", json={"grid": grid}).json()
    assert body["reached"]
    for (r1, c1), (r2, c2) in zip(body["path"], body["path"][1:], strict=False):
        assert abs(r1 - r2) + abs(c1 - c2) <= 1 and grid[r2][c2] == 0


@pytest.mark.parametrize(
    "payload",
    [
        {"grid": [[1, 1, 1, 1, 1], [1, 0, 1, 0, 1], [1, 1, 1, 1, 1]]},  # no path to goal
        {"grid": [[1, 1, 1], [1, 0, 1]]},  # too small
        {"grid": generate("binary_tree", 3, 3, 0.2, seed=1), "level": "medium"},  # classic level
    ],
)
def test_quantum_bot_rejects_invalid_requests(client, payload):
    assert client.post("/api/bot/quantum", json=payload).status_code == 422
