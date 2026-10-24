"""Plain-SQL CRUD for the circuit_runs table (schema in migrations/)."""

from psycopg.types.json import Jsonb

from quantum_app.db import Connection

COLUMNS = "id, circuit, num_qubits, shots, counts, qasm, label, created_at"


def create_run(
    conn: Connection,
    *,
    circuit: str,
    num_qubits: int,
    shots: int,
    counts: dict[str, int],
    qasm: str,
    label: str | None = None,
) -> dict:
    return conn.execute(
        f"""
        INSERT INTO circuit_runs (circuit, num_qubits, shots, counts, qasm, label)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING {COLUMNS}
        """,
        (circuit, num_qubits, shots, Jsonb(counts), qasm, label),
    ).fetchone()


def get_run(conn: Connection, run_id: int) -> dict | None:
    return conn.execute(f"SELECT {COLUMNS} FROM circuit_runs WHERE id = %s", (run_id,)).fetchone()


def list_runs(conn: Connection, *, limit: int = 20, offset: int = 0) -> list[dict]:
    return conn.execute(
        f"""
        SELECT {COLUMNS} FROM circuit_runs
        ORDER BY created_at DESC, id DESC
        LIMIT %s OFFSET %s
        """,
        (limit, offset),
    ).fetchall()


def update_run_label(conn: Connection, run_id: int, label: str | None) -> dict | None:
    return conn.execute(
        f"UPDATE circuit_runs SET label = %s WHERE id = %s RETURNING {COLUMNS}",
        (label, run_id),
    ).fetchone()


def delete_run(conn: Connection, run_id: int) -> bool:
    return conn.execute("DELETE FROM circuit_runs WHERE id = %s", (run_id,)).rowcount > 0
