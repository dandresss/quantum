from collections.abc import Callable

from qiskit import QuantumCircuit, qasm2
from qiskit.primitives import StatevectorSampler


def bell(num_qubits: int = 2) -> QuantumCircuit:
    if num_qubits != 2:
        raise ValueError("bell circuit requires exactly 2 qubits")
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure_all()
    return qc


def ghz(num_qubits: int) -> QuantumCircuit:
    if num_qubits < 2:
        raise ValueError("ghz circuit requires at least 2 qubits")
    qc = QuantumCircuit(num_qubits)
    qc.h(0)
    for target in range(1, num_qubits):
        qc.cx(0, target)
    qc.measure_all()
    return qc


def superposition(num_qubits: int) -> QuantumCircuit:
    if num_qubits < 1:
        raise ValueError("superposition circuit requires at least 1 qubit")
    qc = QuantumCircuit(num_qubits)
    qc.h(range(num_qubits))
    qc.measure_all()
    return qc


CIRCUITS: dict[str, Callable[[int], QuantumCircuit]] = {
    "bell": bell,
    "ghz": ghz,
    "superposition": superposition,
}


def build(name: str, num_qubits: int) -> QuantumCircuit:
    try:
        factory = CIRCUITS[name]
    except KeyError:
        raise ValueError(f"unknown circuit {name!r}") from None
    return factory(num_qubits)


def sample(qc: QuantumCircuit, shots: int, seed: int | None = None) -> dict[str, int]:
    """Run the circuit on the local statevector simulator and return bitstring counts."""
    result = StatevectorSampler(seed=seed).run([qc], shots=shots).result()
    return result[0].data.meas.get_counts()


def to_qasm(qc: QuantumCircuit) -> str:
    return qasm2.dumps(qc)
