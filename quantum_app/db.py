from collections.abc import Iterator

import psycopg
from fastapi import HTTPException
from psycopg.rows import dict_row

from quantum_app.config import get_settings

Connection = psycopg.Connection[dict]


def connect(url: str) -> Connection:
    # Serverless functions are short-lived, so open one connection per request
    # (use Neon's pooled URL in production). prepare_threshold=None disables
    # server-side prepared statements, which PgBouncer transaction mode breaks.
    return psycopg.connect(url, row_factory=dict_row, prepare_threshold=None)


def get_optional_conn() -> Iterator[Connection | None]:
    url = get_settings().database_url
    if not url:
        yield None
        return
    with connect(url) as conn:
        yield conn


def get_conn() -> Iterator[Connection]:
    url = get_settings().database_url
    if not url:
        raise HTTPException(status_code=503, detail="DATABASE_URL is not configured")
    with connect(url) as conn:
        yield conn
