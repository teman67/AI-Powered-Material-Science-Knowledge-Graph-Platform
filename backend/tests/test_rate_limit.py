from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.rate_limit import SimpleRateLimitMiddleware


def test_rate_limit_middleware_blocks_after_limit() -> None:
    app = FastAPI()
    app.add_middleware(SimpleRateLimitMiddleware, requests=2, window_seconds=60, enabled=True)

    @app.get("/limited")
    def limited() -> dict[str, str]:
        return {"ok": "yes"}

    client = TestClient(app)

    first = client.get("/limited")
    second = client.get("/limited")
    third = client.get("/limited")

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 429
