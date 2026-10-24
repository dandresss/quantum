from datetime import datetime
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from quantum_app import circuits, crud
from quantum_app.config import get_settings
from quantum_app.db import Connection, get_conn, get_optional_conn

app = FastAPI(title="Quantum", docs_url="/api/docs", openapi_url="/api/openapi.json")

OptionalConn = Annotated[Connection | None, Depends(get_optional_conn)]
Conn = Annotated[Connection, Depends(get_conn)]


class RunRequest(BaseModel):
    circuit: str = "bell"
    num_qubits: int = Field(2, ge=1)
    shots: int = Field(1024, ge=1)
    seed: int | None = None
    label: str | None = Field(None, max_length=200)
    persist: bool = True


class RunResponse(BaseModel):
    id: int | None
    circuit: str
    num_qubits: int
    shots: int
    counts: dict[str, int]
    qasm: str
    label: str | None = None


class RunRecord(RunResponse):
    id: int
    created_at: datetime


class RunUpdate(BaseModel):
    label: str | None = Field(None, max_length=200)


@app.get("/api/health")
def health(conn: OptionalConn):
    if conn is None:
        db = "not_configured"
    else:
        try:
            conn.execute("SELECT 1")
            db = "ok"
        except Exception:
            db = "error"
    return {"status": "ok", "database": db}


@app.get("/api/circuits")
def list_circuits():
    return {"circuits": sorted(circuits.CIRCUITS)}


@app.post("/api/circuits/run", response_model=RunResponse)
def run_circuit(req: RunRequest, conn: OptionalConn):
    settings = get_settings()
    if req.num_qubits > settings.max_qubits:
        raise HTTPException(422, f"num_qubits must be <= {settings.max_qubits}")
    if req.shots > settings.max_shots:
        raise HTTPException(422, f"shots must be <= {settings.max_shots}")

    try:
        qc = circuits.build(req.circuit, req.num_qubits)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

    result = {
        "circuit": req.circuit,
        "num_qubits": req.num_qubits,
        "shots": req.shots,
        "counts": circuits.sample(qc, req.shots, req.seed),
        "qasm": circuits.to_qasm(qc),
        "label": req.label,
    }
    if req.persist and conn is not None:
        return crud.create_run(conn, **result)
    return {"id": None, **result}


@app.get("/api/runs", response_model=list[RunRecord])
def list_runs(
    conn: Conn,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    return crud.list_runs(conn, limit=limit, offset=offset)


@app.get("/api/runs/{run_id}", response_model=RunRecord)
def get_run(run_id: int, conn: Conn):
    run = crud.get_run(conn, run_id)
    if run is None:
        raise HTTPException(404, "run not found")
    return run


@app.patch("/api/runs/{run_id}", response_model=RunRecord)
def update_run(run_id: int, body: RunUpdate, conn: Conn):
    run = crud.update_run_label(conn, run_id, body.label)
    if run is None:
        raise HTTPException(404, "run not found")
    return run


@app.delete("/api/runs/{run_id}", status_code=204)
def delete_run(run_id: int, conn: Conn):
    if not crud.delete_run(conn, run_id):
        raise HTTPException(404, "run not found")
    return Response(status_code=204)


# On Vercel, public/ is served by the CDN before requests reach this app; the
# mount makes `uvicorn main:app` serve the same frontend locally.
PUBLIC_DIR = Path(__file__).resolve().parent.parent / "public"
if PUBLIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=PUBLIC_DIR, html=True), name="public")
