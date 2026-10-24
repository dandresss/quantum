import pytest

from quantum_app import circuits


def test_bell_is_entangled():
    counts = circuits.sample(circuits.bell(), shots=2000, seed=42)
    assert set(counts) <= {"00", "11"}
    assert sum(counts.values()) == 2000
    assert 800 < counts["00"] < 1200


def test_ghz_outcomes():
    counts = circuits.sample(circuits.ghz(4), shots=200, seed=1)
    assert set(counts) <= {"0000", "1111"}


def test_superposition_covers_all_states():
    counts = circuits.sample(circuits.superposition(2), shots=2000, seed=3)
    assert set(counts) == {"00", "01", "10", "11"}


def test_seed_is_reproducible():
    qc = circuits.superposition(3)
    assert circuits.sample(qc, 100, seed=5) == circuits.sample(qc, 100, seed=5)


def test_unknown_circuit():
    with pytest.raises(ValueError):
        circuits.build("teleport", 2)
