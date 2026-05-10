from time import perf_counter

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

REQUEST_COUNT = Counter(
    "materials_api_requests_total",
    "Total count of API requests",
    ["method", "path", "status"],
)

REQUEST_LATENCY_SECONDS = Histogram(
    "materials_api_request_duration_seconds",
    "API request duration in seconds",
    ["method", "path"],
)


def render_metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


class PrometheusMetricsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: object, enabled: bool = True, metrics_path: str = "/metrics") -> None:
        super().__init__(app)
        self._enabled = enabled
        self._metrics_path = metrics_path

    async def dispatch(self, request: Request, call_next: object) -> Response:
        if not self._enabled or request.url.path == self._metrics_path:
            return await call_next(request)

        started = perf_counter()
        method = request.method
        path = request.url.path

        try:
            response = await call_next(request)
            status = str(response.status_code)
            return response
        except Exception:
            status = "500"
            raise
        finally:
            duration = perf_counter() - started
            REQUEST_COUNT.labels(method=method, path=path, status=status).inc()
            REQUEST_LATENCY_SECONDS.labels(method=method, path=path).observe(duration)
