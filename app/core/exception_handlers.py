import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.core.exceptions import AppException

logger = logging.getLogger("noblink")


def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        body = {"success": False, "message": exc.message}
        if exc.details is not None:
            body["details"] = jsonable_encoder(exc.details)
        return JSONResponse(status_code=exc.status_code, content=body)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": (
                    exc.detail if isinstance(exc.detail, str) else "Request failed."
                ),
                "details": (
                    None
                    if isinstance(exc.detail, str)
                    else jsonable_encoder(exc.detail)
                ),
            },
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(
        request: Request,
        exc: RequestValidationError,
    ):
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "message": "Request validation failed.",
                "details": jsonable_encoder(exc.errors()),
            },
        )

    @app.exception_handler(ValidationError)
    async def pydantic_validation_handler(request: Request, exc: ValidationError):
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": "Data validation failed.",
                "details": jsonable_encoder(exc.errors()),
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception(
            "Unhandled error on %s %s",
            request.method,
            request.url.path,
        )
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "An unexpected error occurred.",
            },
        )
