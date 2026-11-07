"""uvicorn 入口：uvicorn app.server:app --reload"""

from __future__ import annotations

from app.main import create_app

app = create_app()
