"""Laberinto cuántico: cada decisión al azar del generador sale de medir qubits.

Un qubit en superposición (puerta H, la carta del hada) cae en 0 o en 1 con probabilidad 1/2 al
medirlo. Esos bits reemplazan a `random.Random` en los algoritmos de `quantum_app/maze.py`
(binary_tree y backtracker, con braid), así que el laberinto sale en el mismo formato
(1 = pared, 0 = pasillo) y sirve tal cual para el frontend y los bots.

    from quantum_maze import generate
    grid = generate("backtracker", 15, 10, braid=0.2)

En el simulador local la medición la sortea NumPy (`seed` repite el laberinto); en un computador
cuántico real los bits serían aleatorios de verdad.

Ejecutar a mano para verlo: `uv run python quantum_maze.py --width 15 --height 10`
"""

import numpy as np
from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler

from quantum_app.maze import ALGORITHMS

QUBITS = 16  # bits por medición
SHOTS = 256  # mediciones por ejecución: 4096 bits cuánticos por recarga
FLOAT_BITS = 16  # resolución de random(): de sobra para comparar con el braid


def coin_circuit(qubits: int = QUBITS) -> QuantumCircuit:
    """Todos los qubits en superposición uniforme y medidos: `qubits` monedas cuánticas."""
    qc = QuantumCircuit(qubits)
    qc.h(range(qubits))
    qc.measure_all()
    return qc


class QuantumRandom:
    """Lo que usan los algoritmos de `random.Random` (random y choice), con bits cuánticos."""

    def __init__(self, seed: int | None = None):
        # Un Generator y no un int: con un int cada ejecución repetiría los mismos bits
        self.sampler = StatevectorSampler(seed=np.random.default_rng(seed))
        self.circuit = coin_circuit()
        self.bits: list[int] = []
        self.runs = 0  # veces que se ejecutó el circuito
        self.used = 0  # bits cuánticos consumidos

    def bit(self) -> int:
        if not self.bits:
            result = self.sampler.run([self.circuit], shots=SHOTS).result()
            self.bits = [int(b) for shot in result[0].data.meas.get_bitstrings() for b in shot]
            self.runs += 1
        self.used += 1
        return self.bits.pop()

    def integer(self, nbits: int) -> int:
        value = 0
        for _ in range(nbits):
            value = value << 1 | self.bit()
        return value

    def random(self) -> float:
        """Número en [0, 1)."""
        return self.integer(FLOAT_BITS) / 2**FLOAT_BITS

    def choice(self, seq):
        """Elemento uniforme: sortea los bits justos para el índice y repite si se pasa de largo."""
        if not seq:
            raise IndexError("cannot choose from an empty sequence")
        nbits = (len(seq) - 1).bit_length()
        while (i := self.integer(nbits)) >= len(seq):
            pass
        return seq[i]


def generate(
    algorithm: str,
    width: int,
    height: int,
    braid: float = 0.2,
    seed: int | None = None,
    rng: QuantumRandom | None = None,
) -> list[list[int]]:
    """Igual que `quantum_app.maze.generate`, pero con azar cuántico."""
    if width < 1 or height < 1:
        raise ValueError("width and height must be at least 1")
    if not 0.0 <= braid <= 1.0:
        raise ValueError("braid must be between 0 and 1")
    if algorithm not in ALGORITHMS:
        raise ValueError(f"unknown algorithm {algorithm!r}")
    return ALGORITHMS[algorithm](width, height, braid, rng or QuantumRandom(seed))


def render(grid: list[list[int]]) -> str:
    start, goal = (1, 1), (len(grid) - 2, len(grid[0]) - 2)
    marks = {start: "S ", goal: "E "}
    return "\n".join(
        "".join(marks.get((r, c), "██" if cell else "  ") for c, cell in enumerate(row))
        for r, row in enumerate(grid)
    )


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Genera un laberinto con azar cuántico.")
    parser.add_argument("--algorithm", choices=sorted(ALGORITHMS), default="backtracker")
    parser.add_argument("--width", type=int, default=15, help="celdas por fila")
    parser.add_argument("--height", type=int, default=10, help="celdas por columna")
    parser.add_argument("--braid", type=float, default=0.2, help="0-1, ciclos extra")
    parser.add_argument("--seed", type=int, default=None, help="para repetir el laberinto")
    args = parser.parse_args()

    rng = QuantumRandom(args.seed)
    grid = generate(args.algorithm, args.width, args.height, args.braid, rng=rng)
    print(render(grid))
    print(
        f"\n{rng.used} bits cuánticos medidos · {rng.runs} ejecuciones del circuito "
        f"({QUBITS} qubits × {SHOTS} shots)"
    )


if __name__ == "__main__":
    main()
