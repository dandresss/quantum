"""Bot cuántico: el gato decide cada movimiento con el algoritmo de Grover.

No entrena. En cada celda pone las 4 direcciones en superposición (2 qubits) y consulta una
sola vez al laberinto, el oráculo que marca la dirección que acerca a la salida. Con 4 opciones
y 1 marcada, una iteración de Grover da la respuesta con probabilidad 1. Un bot clásico tiene
que probar direcciones de una en una: 2.25 consultas en promedio.

    from quantum_bot import QuantumBot
    bot = QuantumBot(grid, start, goal)
    resultado = bot.play("hard")

Ejecutar a mano compara contra el bot clásico: `uv run python quantum_bot.py --width 12 --height 8`
"""

from collections import deque

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

from agent import ACTIONS

# noise = probabilidad de que la decoherencia arruine la medición (resultado al azar)
LEVELS = {
    "hard": {"noise": 0.05, "tick_ms": 300},
    "expert": {"noise": 0.0, "tick_ms": 240},  # computador cuántico ideal
}

# Consultas que necesita un buscador clásico para hallar 1 dirección marcada entre 4,
# probando sin repetir (la cuarta se deduce): 1/4·1 + 1/4·2 + 2/4·3
CLASSICAL_QUERIES_PER_MOVE = 2.25


def grover_circuit(marked: int, measure: bool = True) -> QuantumCircuit:
    """Una iteración de Grover sobre 2 qubits (4 direcciones) con `marked` como solución."""
    qc = QuantumCircuit(2)
    qc.h([0, 1])
    # Oráculo: invierte la fase de |marked>
    zeros = [q for q in range(2) if not (marked >> q) & 1]
    if zeros:
        qc.x(zeros)
    qc.cz(0, 1)
    if zeros:
        qc.x(zeros)
    # Difusor: reflexión sobre la superposición uniforme
    qc.h([0, 1])
    qc.x([0, 1])
    qc.cz(0, 1)
    qc.x([0, 1])
    qc.h([0, 1])
    if measure:
        qc.measure_all()
    return qc


# Distribución de la medición para cada dirección marcada (se simula una sola vez)
MEASURE_PROBS = [Statevector(grover_circuit(m, measure=False)).probabilities() for m in range(4)]


class QuantumBot:
    def __init__(self, grid, start, goal, seed=None):
        """grid: lista de listas (1 = pared, 0 = pasillo). start/goal: (fila, col)."""
        self.grid, self.start, self.goal = np.array(grid), tuple(start), tuple(goal)
        self.rng = np.random.default_rng(seed)
        self.dist = self._distances()
        if self.start not in self.dist:
            raise ValueError("No hay camino de start a goal")

    def _distances(self):
        """BFS desde la salida: es lo que 'sabe' el laberinto, consultado por el oráculo."""
        h, w = self.grid.shape
        dist, q = {self.goal: 0}, deque([self.goal])
        while q:
            r, c = q.popleft()
            for dr, dc in ACTIONS:
                n = (r + dr, c + dc)
                if 0 <= n[0] < h and 0 <= n[1] < w and self.grid[n] == 0 and n not in dist:
                    dist[n] = dist[(r, c)] + 1
                    q.append(n)
        return dist

    def oracle(self, s):
        """Dirección que acerca a la salida. Si hay empate (ciclos), marca solo la primera:
        con 2 marcadas entre 4, Grover no amplifica nada."""
        for a, (dr, dc) in enumerate(ACTIONS):
            if self.dist.get((s[0] + dr, s[1] + dc)) == self.dist[s] - 1:
                return a
        raise AssertionError("celda sin vecino más cercano a la salida")

    def measure(self, marked, noise):
        if self.rng.random() < noise:
            return int(self.rng.integers(4))
        return int(self.rng.choice(4, p=MEASURE_PROBS[marked]))

    def play(self, level="hard"):
        """Una partida: trayectoria del bot (celdas repetidas = chocó con una pared)."""
        cfg = LEVELS[level]
        h, w = self.grid.shape
        max_steps = int(3 * (self.grid == 0).sum())
        s, path = self.start, [self.start]
        while s != self.goal and len(path) <= max_steps:
            dr, dc = ACTIONS[self.measure(self.oracle(s), cfg["noise"])]
            n = (s[0] + dr, s[1] + dc)
            if 0 <= n[0] < h and 0 <= n[1] < w and self.grid[n] == 0:
                s = n
            path.append(s)
        moves = len(path) - 1
        return {
            "path": [list(p) for p in path],
            "reached": s == self.goal,
            "steps": moves,
            "tick_ms": cfg["tick_ms"],
            "queries": {"quantum": moves, "classical_expected": moves * CLASSICAL_QUERIES_PER_MOVE},
        }


def render(grid, path):
    trail = {tuple(p) for p in path}
    start, goal = tuple(path[0]), (len(grid) - 2, len(grid[0]) - 2)
    lines = []
    for r, row in enumerate(grid):
        line = []
        for c, cell in enumerate(row):
            if (r, c) == start:
                line.append("S ")
            elif (r, c) == goal:
                line.append("E ")
            elif (r, c) in trail:
                line.append("··")
            else:
                line.append("██" if cell else "  ")
        lines.append("".join(line))
    return "\n".join(lines)


def main() -> None:
    import argparse

    from bot import BotRival
    from quantum_app.maze import ALGORITHMS, generate

    parser = argparse.ArgumentParser(description="Bot cuántico (Grover) contra el bot clásico.")
    parser.add_argument("--algorithm", choices=sorted(ALGORITHMS), default="backtracker")
    parser.add_argument("--width", type=int, default=12, help="celdas por fila")
    parser.add_argument("--height", type=int, default=8, help="celdas por columna")
    parser.add_argument("--braid", type=float, default=0.2, help="0-1, ciclos extra")
    parser.add_argument("--seed", type=int, default=None, help="para repetir el laberinto")
    parser.add_argument("--level", choices=sorted(LEVELS), default="hard")
    args = parser.parse_args()

    grid = generate(args.algorithm, args.width, args.height, args.braid, seed=args.seed)
    start, goal = (1, 1), (len(grid) - 2, len(grid[0]) - 2)

    quantum = QuantumBot(grid, start, goal, seed=args.seed).play(args.level)
    classic = BotRival(grid, start, goal).play("medium")
    shortest = QuantumBot(grid, start, goal).dist[start]

    print(render(grid, quantum["path"]))
    print(f"\nCamino más corto: {shortest} pasos")
    bots = (("Clásico (Q-learning, medium)", classic), (f"Cuántico ({args.level})", quantum))
    for name, res in bots:
        status = "escapó" if res["reached"] else "no escapó"
        time_s = res["steps"] * res["tick_ms"] / 1000
        print(f"{name:30} {status} en {res['steps']:4} pasos · {time_s:5.1f} s en pantalla")
    q = quantum["queries"]
    print(
        f"Consultas al oráculo: Grover {q['quantum']} · "
        f"búsqueda clásica ~{q['classical_expected']:.0f}"
    )


if __name__ == "__main__":
    main()
