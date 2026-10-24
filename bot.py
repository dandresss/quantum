"""Fachada para usar el bot rival desde cualquier parte del backend.

    from bot import BotRival
    bot = BotRival(grid, start, goal)      # entrena una vez (segundos)
    resultado = bot.play("medium")         # úsalo en cada partida
"""
import numpy as np
from agent import QAgent

# Dificultad = cuánto entrenó (fracción de los episodios) + cuánto se equivoca + velocidad en pantalla
# eps 0.15: el 85% de los movimientos obedece al algoritmo y el 15% es aleatorio (a una celda libre)
LEVELS = {
    "easy":   {"train_frac": 0.05, "eps": 0.15, "tick_ms": 420},   # básica
    "medium": {"train_frac": 0.10, "eps": 0.15, "tick_ms": 360},   # media
}


class BotRival:
    def __init__(self, grid, start, goal, episodes=None, seed=1):
        """grid: lista de listas (1 = pared, 0 = pasillo). start/goal: (fila, col).
        episodes=None -> se calcula según el tamaño (mapas grandes necesitan más entrenamiento)."""
        if episodes is None:
            episodes = int(400 * max(1.0, self._shortest(grid, start, goal) / 52))   # 400 está calibrado para un camino de 52 pasos
        self.agent = QAgent(grid, start, goal, seed=seed)
        marks = {lv: max(1, int(episodes * c["train_frac"])) for lv, c in LEVELS.items()}
        snaps, self.history = self.agent.train(episodes, snapshots=set(marks.values()))
        self.Q = {lv: snaps[ep] for lv, ep in marks.items()}

    @staticmethod
    def _shortest(grid, start, goal):
        """Largo del camino más corto (BFS). Solo sirve para escalar el entrenamiento."""
        from collections import deque
        h, w = len(grid), len(grid[0]); q = deque([(tuple(start), 0)]); seen = {tuple(start)}
        while q:
            (r, c), d = q.popleft()
            if (r, c) == tuple(goal):
                return d
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (r + dr, c + dc)
                if 0 <= n[0] < h and 0 <= n[1] < w and grid[n[0]][n[1]] == 0 and n not in seen:
                    seen.add(n); q.append((n, d + 1))
        raise ValueError("No hay camino de start a goal")

    def play(self, level="medium", with_heatmap=False):
        """Una partida: trayectoria del bot (celdas repetidas = chocó con una pared)."""
        cfg = LEVELS[level]
        path, reached = self.agent.rollout(self.Q[level], cfg["eps"])
        out = {"path": [list(p) for p in path], "reached": reached,
               "steps": len(path) - 1, "tick_ms": cfg["tick_ms"]}
        if with_heatmap:
            out["heatmap"] = self.heatmap(level)
        return out

    def heatmap(self, level="medium"):
        Q, g = self.Q[level], self.agent.grid
        v = Q.max(axis=2)
        mask = (g == 0) & (np.abs(Q).sum(axis=2) > 0)
        lo, hi = v[mask].min(), v[mask].max()
        n = (v - lo) / (hi - lo + 1e-9)
        return [[round(float(n[r, c]), 2) if mask[r, c] else None for c in range(g.shape[1])]
                for r in range(g.shape[0])]
