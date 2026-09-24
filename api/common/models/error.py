import datetime
from typing import Annotated, Any

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, ValidationError


class ValidationDetail(BaseModel):
    error_code: Annotated[str, Field()]
    field: Annotated[tuple[str | int, ...], Field()]
    msg: Annotated[str, Field()]
    ctx: Annotated[Any, Field()]


class ErrorResponse(BaseModel):
    time: Annotated[datetime.datetime, Field()]
    path: Annotated[str, Field()]
    method: Annotated[str, Field()]
    type: Annotated[str, Field()]
    message: Annotated[str, Field()]
    details: list[ValidationDetail] = Field(default_factory=list)

    def __init__(
        self,
        request: Request,
        exception: Exception | RequestValidationError | ValidationError,
        **data,
    ) -> None:
        data["message"] = (
            data.get("message", None)
            or str(
                getattr(exception, "msg", None)
                or getattr(exception, "detail", None)
                or exception
            )
            or "An error occurred"
        )

        if isinstance(exception, (RequestValidationError, ValidationError)):
            data["message"] = "The request failed due to validation errors"

            data["details"] = [
                ValidationDetail(
                    error_code=error["type"],
                    field=error["loc"],
                    msg=error["msg"],
                    ctx=jsonable_encoder(error["ctx"]) if "ctx" in error else {},
                )
                for error in exception.errors()
            ]

        super().__init__(
            time=datetime.datetime.now(datetime.UTC),
            path=str(request.url),
            method=request.method,
            type=type(exception).__name__,
            **data,
        )
