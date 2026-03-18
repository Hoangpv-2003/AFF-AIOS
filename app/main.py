from __future__ import annotations

"""FastAPI application entrypoint."""

import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.constants import REQUEST_ID_HEADER, TRACE_ID_HEADER
from app.infrastructure.observability.tracing import (
    configure_tracer,
    get_tracer,
)


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
    configure_tracer(service_name="aaf-aios-api")
    tracer = get_tracer()

    @app.middleware("http")
    async def request_context_middleware(request: Request, call_next):
        start = time.perf_counter()
        request_id = request.headers.get(REQUEST_ID_HEADER, str(uuid.uuid4()))
        trace_id = request.headers.get(TRACE_ID_HEADER, request_id)
        root_span_id = tracer.start_span(
            trace_id=trace_id,
            name=f"http.{request.method}.{request.url.path}",
            kind="server",
            attributes={"path": request.url.path, "method": request.method},
        )
        request.state.request_id = request_id
        request.state.trace_id = trace_id
        request.state.root_span_id = root_span_id
        try:
            response = await call_next(request)
        except Exception as exc:  # pragma: no cover
            tracer.add_event(
                trace_id=trace_id,
                span_id=root_span_id,
                name="http.exception",
                message=str(exc),
            )
            tracer.end_span(root_span_id, status="error")
            return JSONResponse(
                status_code=500,
                content={
                    "code": "internal_error",
                    "message": str(exc),
                    "details": {},
                    "trace_id": trace_id,
                    "retryable": False,
                },
            )
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        tracer.end_span(
            root_span_id,
            status="ok",
            attributes={
                "status_code": response.status_code,
                "elapsed_ms": elapsed_ms,
            },
        )
        response.headers[REQUEST_ID_HEADER] = request_id
        response.headers[TRACE_ID_HEADER] = trace_id
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

    frontend_dir = Path(__file__).resolve().parent / "frontend"
    if frontend_dir.exists():
        app.mount(
            "/frontend",
            StaticFiles(directory=str(frontend_dir), html=True),
            name="frontend",
        )

    reports_dir = Path(__file__).resolve().parents[1] / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    app.mount(
        "/reports",
        StaticFiles(directory=str(reports_dir), html=False),
        name="reports",
    )

    @app.get("/")
    async def root() -> RedirectResponse:
        return RedirectResponse(url="/frontend")

    app.include_router(api_router)
    return app


app = create_app()
