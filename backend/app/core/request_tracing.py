import logging
from contextvars import ContextVar
from time import perf_counter
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_request_id_context: ContextVar[str] = ContextVar("request_id", default="-")


def get_request_id() -> str:
    return _request_id_context.get()


class RequestIdLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True


def configure_application_logging(level_name: str = "INFO") -> None:
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s [request_id=%(request_id)s] %(name)s %(message)s"
            )
        )
        root_logger.addHandler(handler)

    for handler in root_logger.handlers:
        if not any(isinstance(log_filter, RequestIdLogFilter) for log_filter in handler.filters):
            handler.addFilter(RequestIdLogFilter())

    root_logger.setLevel(getattr(logging, level_name.upper(), logging.INFO))


class RequestTracingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: object, header_name: str = "X-Request-ID", enabled: bool = True) -> None:
        super().__init__(app)
        self._header_name = header_name
        self._enabled = enabled
        self._logger = logging.getLogger("app.request")

    async def dispatch(self, request: Request, call_next: object) -> Response:
        if not self._enabled:
            return await call_next(request)

        incoming_request_id = request.headers.get(self._header_name)
        request_id = incoming_request_id.strip() if incoming_request_id and incoming_request_id.strip() else uuid4().hex

        token = _request_id_context.set(request_id)
        request.state.request_id = request_id
        started = perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = (perf_counter() - started) * 1000
            self._logger.exception(
                "request_failed method=%s path=%s duration_ms=%.2f",
                request.method,
                request.url.path,
                elapsed_ms,
            )
            raise
        else:
            elapsed_ms = (perf_counter() - started) * 1000
            self._logger.info(
                "request_completed method=%s path=%s status_code=%s duration_ms=%.2f",
                request.method,
                request.url.path,
                response.status_code,
                elapsed_ms,
            )
            response.headers[self._header_name] = request_id
            return response
        finally:
            _request_id_context.reset(token)
