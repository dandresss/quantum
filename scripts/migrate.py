"""Apply pending migrations/*.sql files in order.

Usage: uv run python scripts/migrate.py            (uses DATABASE_URL / .env)
       uv run python scripts/migrate.py <url>
"""

import sys
from pathlib import Path

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from quantum_app.config import get_settings  # noqa: E402

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def migrate(url: str) -> list[str]:
    applied_now = []
    with psycopg.connect(url) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                name       TEXT PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        # Serialize concurrent runs (e.g. two deploys) on an advisory lock.
        conn.execute("SELECT pg_advisory_xact_lock(hashtext('schema_migrations'))")
        done = {row[0] for row in conn.execute("SELECT name FROM schema_migrations")}
        for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
            if path.name in done:
                continue
            conn.execute(path.read_text())
            conn.execute("INSERT INTO schema_migrations (name) VALUES (%s)", (path.name,))
            applied_now.append(path.name)
    return applied_now


def main() -> None:
    url = sys.argv[1] if len(sys.argv) > 1 else get_settings().database_url
    if not url:
        sys.exit("DATABASE_URL is not set (env var, .env, or first argument)")
    applied = migrate(url)
    print("\n".join(f"applied {name}" for name in applied) or "database is up to date")


if __name__ == "__main__":
    main()
