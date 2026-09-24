import logging
import traceback

from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from opencensus.trace import execution_context
from opencensus.trace.attributes_helper import COMMON_ATTRIBUTES
from starlette.types import ASGIApp, Receive, Scope, Send

from common.config import settings
from common.exceptions import InternalServerError
from common.models.error import ErrorResponse

log = logging.getLogger(__name__)


class ExceptionTracebackMiddleware:
    """Middleware for unhandled exceptions: sets tracing attributes, logs exception traceback, returns error response"""

    def __init__(
        self,
        app: ASGIApp,
    ) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        try:
            await self.app(scope, receive, send)
            return
        except Exception as exc:  # pylint: disable=broad-except
            self.add_traceback_attributes(exc)

            query_string = scope.get("query_string")
            log.error(
                "%s %s%s -> %s",
                scope.get("method"),
                scope.get("path"),
                "?" + query_string.decode("utf-8") if query_string else "",
                exc,
                exc_info=exc,
            )

            msg = None
            if settings.app_debug:
                msg = exc

            response = JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=jsonable_encoder(
                    ErrorResponse(Request(scope), InternalServerError(msg))
                ),
            )

            await response(scope, receive, send)
            return

    @staticmethod
    def add_traceback_attributes(exception):
        """adds traceback attributes to current Span of tracing context"""

        if span := execution_context.get_current_span():
            span.add_attribute(
                COMMON_ATTRIBUTES["ERROR_NAME"], exception.__class__.__name__
            )

            span.add_attribute(COMMON_ATTRIBUTES["ERROR_MESSAGE"], str(exception))

            span.add_attribute(
                COMMON_ATTRIBUTES["STACKTRACE"],
                "\n".join(
                    traceback.format_tb(
                        exception.__traceback__,
                        limit=settings.traceback_max_entries * -1,
                    )
                ),
            )
