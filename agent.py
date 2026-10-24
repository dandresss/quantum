"""Bot clásico: Q-Learning tabular sobre un laberinto estático."""
import numpy as np

ACTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]     # arriba, abajo, izquierda, derecha


class QAgent:
    def __init__(self, grid, start, goal, alpha=0.5, gamma=0.95, seed=0):
        self.grid, self.start, self.goal = np.array(grid), tuple(start), tuple(goal)
        self.alpha, self.gamma = alpha, gamma
        self.Q = np.zeros((*self.grid.shape, 4))  # Q[fila, col, acción]
        self.rng = np.random.default_rng(seed)

    # ---- entorno -------------------------------------------------------
    def step(self, s, a):
        nr, nc = s[0] + ACTIONS[a][0], s[1] + ACTIONS[a][1]
        h, w = self.grid.shape
        if not (0 <= nr < h and 0 <= nc < w) or self.grid[nr, nc] == 1:   # pared o borde: se queda y pierde
            return s, -3.0, False
        if (nr, nc) == self.goal:
            return (nr, nc), 100.0, True
        return (nr, nc), -1.0, False             # cada paso cuesta tiempo

    # ---- política ε-greedy ----------------------------------------------
    def choose(self, s, eps, Q=None):
        Q = self.Q if Q is None else Q
        if self.rng.random() < eps:
            return int(self.rng.integers(4))
        q = Q[s]
        return int(self.rng.choice(np.flatnonzero(q == q.max())))

    # ---- entrenamiento -------------------------------------------------
    def train(self, episodes, max_steps=3000, snapshots=()):
        snaps, history = {}, []
        for ep in range(1, episodes + 1):
            eps = max(0.05, 1.0 - ep / (episodes * 0.5))   # explora -> explota
            s = self.start
            for t in range(max_steps):
                a = self.choose(s, eps)
                s2, r, done = self.step(s, a)
                target = r if done else r + self.gamma * self.Q[s2].max()
                self.Q[s][a] += self.alpha * (target - self.Q[s][a])   # regla de Q-Learning
                s = s2
                if done:
                    break
            history.append(t + 1)
            if ep in snapshots:
                snaps[ep] = self.Q.copy()
        return snaps, history

    # ---- partida: devuelve la trayectoria que seguirá el bot -----------
    def rollout(self, Q, eps, max_steps=None):
        max_steps = max_steps or int(3 * (self.grid == 0).sum())   # límite según tamaño del mapa
        s, path = self.start, [self.start]
        for _ in range(max_steps):
            s, _, done = self.step(s, self.choose(s, eps, Q))
            path.append(s)
            if done:
                return path, True
        return path, False
