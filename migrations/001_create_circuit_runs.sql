CREATE TABLE circuit_runs (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    circuit     TEXT        NOT NULL,
    num_qubits  INTEGER     NOT NULL CHECK (num_qubits > 0),
    shots       INTEGER     NOT NULL CHECK (shots > 0),
    counts      JSONB       NOT NULL,
    qasm        TEXT        NOT NULL,
    label       TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX circuit_runs_created_at_idx ON circuit_runs (created_at DESC);
