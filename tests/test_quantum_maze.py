from collections import Counter, deque

import pytest

from quantum_maze import QUBITS, SHOTS, QuantumRandom, coin_circuit, generate


def reachable(grid):
    seen, queue = {(1, 1)}, deque([(1, 1)])
    while queue:
        r, c = queue.popleft()
        for n in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if grid[n[0]][n[1]] == 0 and n not in seen:
                seen.add(n)
                queue.append(n)
    return seen


@pytest.mark.parametrize("algorithm", ["binary_tree", "backtracker"])
def test_perfect_maze_connects_every_cell(algorithm):
    width, height = 6, 4
    grid = generate(algorithm, width, height, braid=0.0, seed=1)
    assert len(grid) == 2 * height + 1 and len(grid[0]) == 2 * width + 1
    open_squares = sum(row.count(0) for row in grid)
    cells = width * height
    assert open_squares == cells + (cells - 1)  # a spanning tree: no loops
    assert len(reachable(grid)) == open_squares


def test_seed_repeats_the_maze():
    assert generate("backtracker", 8, 5, seed=7) == generate("backtracker", 8, 5, seed=7)
    assert generate("backtracker", 8, 5, seed=7) != generate("backtracker", 8, 5, seed=8)


def test_refills_bring_new_bits():
    rng = QuantumRandom(seed=0)
    first = [rng.bit() for _ in range(QUBITS * SHOTS)]
    second = [rng.bit() for _ in range(QUBITS * SHOTS)]
    assert rng.runs == 2 and first != second


def test_choice_is_uniform_and_in_range():
    rng = QuantumRandom(seed=0)
    counts = Counter(rng.choice("abc") for _ in range(3000))
    assert set(counts) == {"a", "b", "c"}
    assert all(800 < n < 1200 for n in counts.values())


def test_coin_circuit_puts_every_qubit_in_superposition():
    qc = coin_circuit(3)
    assert [i.operation.name for i in qc.data].count("h") == 3
    assert qc.num_clbits == 3


def test_rejects_bad_parameters():
    with pytest.raises(ValueError):
        generate("prim", 5, 5)
    with pytest.raises(ValueError):
        generate("backtracker", 5, 5, braid=2)
