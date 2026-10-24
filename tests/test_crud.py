from quantum_app import crud


def _create(conn, **overrides):
    data = {
        "circuit": "bell",
        "num_qubits": 2,
        "shots": 10,
        "counts": {"00": 6, "11": 4},
        "qasm": "OPENQASM 2.0;",
    } | overrides
    return crud.create_run(conn, **data)


def test_create_and_get(conn):
    run = _create(conn, label="x")
    assert run["counts"] == {"00": 6, "11": 4}
    assert crud.get_run(conn, run["id"]) == run


def test_list_newest_first_with_pagination(conn):
    ids = [_create(conn)["id"] for _ in range(3)]
    assert [r["id"] for r in crud.list_runs(conn)] == ids[::-1]
    assert [r["id"] for r in crud.list_runs(conn, limit=1, offset=1)] == [ids[1]]


def test_update_and_delete(conn):
    run = _create(conn)
    assert crud.update_run_label(conn, run["id"], "new")["label"] == "new"
    assert crud.update_run_label(conn, 999_999, "new") is None
    assert crud.delete_run(conn, run["id"]) is True
    assert crud.delete_run(conn, run["id"]) is False
    assert crud.get_run(conn, run["id"]) is None
