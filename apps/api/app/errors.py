"""RFC 9457 Problem Details for every error response."""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

log = structlog.get_logger()

PROBLEM_TYPE_BASE = "https://docs.market-intel.app/errors/"


class AppError(Exception):
    def __init__(
        self,
        status: int,
        code: str,
        title: str,
        detail: str | None = None,
        fields: dict[str, str] | None = None,
    ) -> None:
        super().__init__(title)
        self.status = status
        self.code = code
        self.title = title
        self.detail = detail
        self.fields = fields


def not_found(what: str = "Resurs") -> AppError:
    return AppError(404, "NOT_FOUND", f"{what} topilmadi")


def _problem(
    request: Request, status: int, code: str, title: str, detail: str | None = None, **extra: Any
) -> JSONResponse:
    body: dict[str, Any] = {
        "type": PROBLEM_TYPE_BASE + code.lower().replace("_", "-"),
        "title": title,
        "status": status,
        "code": code,
        "request_id": getattr(request.state, "request_id", None),
    }
    if detail:
        body["detail"] = detail
    body.update({k: v for k, v in extra.items() if v is not None})
    return JSONResponse(body, status_code=status, media_type="application/problem+json")


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(request: Request, exc: AppError) -> JSONResponse:
        return _problem(request, exc.status, exc.code, exc.title, exc.detail, fields=exc.fields)

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        fields = {".".join(str(p) for p in e["loc"] if p != "body"): e["msg"] for e in exc.errors()}
        return _problem(request, 422, "VALIDATION_ERROR", "Kiritilgan ma’lumot noto‘g‘ri", fields=fields)

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = {401: "UNAUTHORIZED", 403: "FORBIDDEN", 404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}.get(
            exc.status_code, "HTTP_ERROR"
        )
        return _problem(request, exc.status_code, code, str(exc.detail))

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        # Never leak internals (or user data) in the response; details go to the log only.
        log.exception("unhandled_error", path=request.url.path)
        return _problem(request, 500, "INTERNAL_ERROR", "Ichki xatolik. Keyinroq qayta urinib ko‘ring.")
