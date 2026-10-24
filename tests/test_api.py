import pytest


def test_health_without_db(client):
    assert client.get("/api/health").json() == {"status": "ok", "database": "not_configured"}


def test_list_circuits(client):
    assert client.get("/api/circuits").json() == {"circuits": ["bell", "ghz", "superposition"]}


def test_run_bell_without_db(client):
    resp = client.post("/api/circuits/run", json={"circuit": "bell", "shots": 500, "seed": 1})
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] is None
    assert set(body["counts"]) <= {"00", "11"}
    assert sum(body["counts"].values()) == 500
    assert body["qasm"].startswith("OPENQASM 2.0;")


@pytest.mark.parametrize(
    "payload",
    [
        {"circuit": "nope"},
        {"circuit": "bell", "num_qubits": 3},
        {"circuit": "ghz", "num_qubits": 99},
        {"circuit": "bell", "shots": 10**9},
        {"circuit": "bell", "shots": 0},
    ],
)
def test_run_rejects_invalid(client, payload):
    assert client.post("/api/circuits/run", json=payload).status_code == 422


def test_runs_require_db(client, monkeypatch):
    from quantum_app.config import get_settings

    monkeypatch.setattr(get_settings(), "database_url", None)
    assert client.get("/api/runs").status_code == 503


# --- with a real PostgreSQL (TEST_DATABASE_URL) ---


def test_health_with_db(db_client):
    assert db_client.get("/api/health").json()["database"] == "ok"


def test_run_crud_flow(db_client):
    resp = db_client.post(
        "/api/circuits/run", json={"circuit": "ghz", "num_qubits": 3, "seed": 7, "label": "first"}
    )
    assert resp.status_code == 200
    run_id = resp.json()["id"]
    assert run_id is not None

    runs = db_client.get("/api/runs").json()
    assert [r["id"] for r in runs] == [run_id]
    assert set(runs[0]["counts"]) <= {"000", "111"}

    assert db_client.get(f"/api/runs/{run_id}").json()["label"] == "first"

    patched = db_client.patch(f"/api/runs/{run_id}", json={"label": "renamed"})
    assert patched.status_code == 200
    assert patched.json()["label"] == "renamed"

    assert db_client.delete(f"/api/runs/{run_id}").status_code == 204
    assert db_client.get(f"/api/runs/{run_id}").status_code == 404
    assert db_client.delete(f"/api/runs/{run_id}").status_code == 404


def test_run_without_persist(db_client):
    resp = db_client.post("/api/circuits/run", json={"persist": False})
    assert resp.json()["id"] is None
    assert db_client.get("/api/runs").json() == []
