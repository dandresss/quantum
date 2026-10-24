# Quantum

API + frontend para simular circuitos cuánticos con **Qiskit**, servida con **FastAPI** en
**Vercel** y con historial de ejecuciones en **PostgreSQL** (SQL plano con `psycopg`, sin ORM).

Producción: https://quantum-iota-ashen.vercel.app

## Estructura

```
main.py                  # entrypoint de Vercel (exporta `app`)
quantum_app/
  api.py                 # rutas FastAPI (/api/...)
  circuits.py            # circuitos Qiskit + simulación (StatevectorSampler)
  crud.py                # CRUD en SQL plano sobre circuit_runs
  db.py                  # conexión psycopg (una por request, apta para serverless)
  config.py              # settings desde env / .env
migrations/*.sql         # migraciones SQL, aplicadas en orden
scripts/migrate.py       # runner de migraciones (tabla schema_migrations)
public/index.html        # frontend estático (CDN de Vercel)
tests/                   # pytest
```

## API

| Método | Ruta                 | Descripción                                   |
| ------ | -------------------- | --------------------------------------------- |
| GET    | `/api/health`        | Estado de la API y de la BD                   |
| GET    | `/api/maze`          | Genera un laberinto (`algorithm`=`binary_tree`\|`backtracker`, `width`, `height`, `braid` 0–1, `seed`) |
| GET    | `/api/circuits`      | Circuitos disponibles (`bell`, `ghz`, `superposition`) |
| POST   | `/api/circuits/run`  | Ejecuta un circuito y (opcional) lo guarda    |
| GET    | `/api/runs`          | Lista ejecuciones (`limit`, `offset`)         |
| GET    | `/api/runs/{id}`     | Detalle de una ejecución                      |
| PATCH  | `/api/runs/{id}`     | Cambia la etiqueta                            |
| DELETE | `/api/runs/{id}`     | Borra la ejecución                            |

Docs interactivas en `/api/docs`.

```bash
curl -X POST localhost:8000/api/circuits/run \
  -H 'content-type: application/json' \
  -d '{"circuit": "ghz", "num_qubits": 3, "shots": 1024, "label": "prueba"}'
```

## Desarrollo local

Requisitos: [uv](https://docs.astral.sh/uv/) y PostgreSQL.

```bash
uv sync                                   # crea .venv con Python 3.12
cp .env.example .env                      # ajusta DATABASE_URL

# Base de datos local (una sola vez)
sudo -u postgres psql -c "CREATE ROLE quantum LOGIN PASSWORD 'quantum';"
sudo -u postgres createdb -O quantum quantum
sudo -u postgres createdb -O quantum quantum_test

uv run python scripts/migrate.py          # aplica migrations/*.sql
uv run uvicorn main:app --reload          # http://localhost:8000
```

Sin `DATABASE_URL` la API sigue funcionando: simula circuitos pero no guarda historial
(`/api/runs` responde 503).

### Tests y lint

```bash
uv run pytest            # los tests de BD se saltan si no hay TEST_DATABASE_URL
uv run ruff check . && uv run ruff format --check .
```

`TEST_DATABASE_URL` debe apuntar a una base desechable: los tests hacen `TRUNCATE`.

### Migraciones

Añade un archivo nuevo `migrations/NNN_descripcion.sql` (numeración creciente) y ejecuta
`uv run python scripts/migrate.py [DATABASE_URL]`. Las ya aplicadas quedan registradas en
`schema_migrations` y no se repiten.

## Deploy (GitHub + Vercel + Postgres)

1. **GitHub**: crea el repo y sube `main`. El workflow `.github/workflows/ci.yml` corre ruff y
   pytest (con un Postgres de servicio) en cada push/PR.
2. **Vercel**: *Add New → Project → Import* el repo de GitHub. Detecta FastAPI desde
   `pyproject.toml`/`uv.lock` y `main.py`; no hace falta `vercel.json`. Cada push a `main`
   despliega a producción y cada PR genera un preview.
3. **Postgres**: en el proyecto de Vercel, *Storage → Create → Neon (Postgres)* y conéctalo a
   los entornos. Eso inyecta `DATABASE_URL` (conexión pooled).
4. **Migrar la BD de producción** desde tu máquina:
   ```bash
   vercel env pull .env.production.local   # o copia DATABASE_URL desde el dashboard
   uv run python scripts/migrate.py "<DATABASE_URL de producción>"
   ```

Notas:
- El bundle de producción (Qiskit + NumPy + SciPy) ronda los 230 MB; el límite de Vercel para
  funciones Python es 500 MB. `.vercelignore` excluye tests, scripts y migraciones.
- La simulación es CPU‑bound: los límites `MAX_QUBITS` (12) y `MAX_SHOTS` (10000) evitan
  timeouts de la función.
