from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.request_tracing import RequestTracingMiddleware, get_request_id


def _build_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestTracingMiddleware, header_name="X-Request-ID", enabled=True)

    @app.get("/ping")
    def ping() -> dict[str, str]:
        return {"request_id": get_request_id()}

    return app


def test_request_tracing_adds_response_header_when_missing() -> None:
    client = TestClient(_build_app())
    response = client.get("/ping")

    assert response.status_code == 200
    response_request_id = response.headers.get("X-Request-ID")
    assert response_request_id
    assert response.json()["request_id"] == response_request_id


def test_request_tracing_preserves_supplied_request_id() -> None:
    client = TestClient(_build_app())
    request_id = "trace-test-id-123"

    response = client.get("/ping", headers={"X-Request-ID": request_id})

    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == request_id
    assert response.json()["request_id"] == request_id
