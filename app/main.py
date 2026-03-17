from __future__ import annotations

"""FastAPI application entrypoint."""

import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.constants import REQUEST_ID_HEADER


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.started = True
        app.state.start_time = time.time()
        try:
            yield
        finally:
            app.state.started = False

    app = FastAPI(title="AAF-AIOS", version="0.1.0", lifespan=lifespan)

    @app.middleware("http")
    async def request_context_middleware(request: Request, call_next):
        start = time.perf_counter()
        request_id = request.headers.get(REQUEST_ID_HEADER, str(uuid.uuid4()))
        request.state.request_id = request_id
        try:
            response = await call_next(request)
        except Exception as exc:  # pragma: no cover
            return JSONResponse(
                status_code=500,
                content={
                    "code": "internal_error",
                    "message": str(exc),
                    "details": {},
                    "trace_id": request_id,
                    "retryable": False,
                },
            )
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        response.headers[REQUEST_ID_HEADER] = request_id
        response.headers["X-Response-Time-Ms"] = str(elapsed_ms)
        return response

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/ready")
    async def ready() -> dict[str, str]:
        started = getattr(app.state, "started", False)
        status = "ready" if started else "not_ready"
        return {"status": status}

    app.include_router(api_router)
    return app


app = create_app()

