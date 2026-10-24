# Vercel entrypoint: the Python runtime detects the ASGI `app` exported here.
# Local dev: `uv run uvicorn main:app --reload`
from quantum_app.api import app

__all__ = ["app"]
