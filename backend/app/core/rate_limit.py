from collections import deque
from dataclasses import dataclass
from threading import Lock
from time import monotonic

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response


@dataclass
class _RateEntry:
    timestamps: deque[float]


class SimpleRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: object, requests: int, window_seconds: int, enabled: bool = True) -> None:
        super().__init__(app)
        self._requests = requests
        self._window_seconds = window_seconds
        self._enabled = enabled
        self._lock = Lock()
        self._store: dict[str, _RateEntry] = {}

    async def dispatch(self, request: Request, call_next: object) -> Response:
        if not self._enabled or self._should_skip(request.url.path):
            return await call_next(request)

        key = self._request_key(request)
        now = monotonic()

        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                entry = _RateEntry(timestamps=deque())
                self._store[key] = entry

            while entry.timestamps and now - entry.timestamps[0] > self._window_seconds:
                entry.timestamps.popleft()

            if len(entry.timestamps) >= self._requests:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded. Please retry later."},
                    headers={"Retry-After": str(self._window_seconds)},
                )

            entry.timestamps.append(now)

        return await call_next(request)

    def _request_key(self, request: Request) -> str:
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            client_ip = forwarded_for.split(",", maxsplit=1)[0].strip()
        elif request.client is not None:
            client_ip = request.client.host
        else:
            client_ip = "unknown"

        return f"{client_ip}:{request.url.path}"

    @staticmethod
    def _should_skip(path: str) -> bool:
        return path.startswith("/health")
