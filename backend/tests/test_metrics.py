from fastapi.testclient import TestClient

from app.main import app


def test_metrics_endpoint_exposes_prometheus_content() -> None:
    client = TestClient(app)
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "materials_api_requests_total" in response.text


def test_metrics_counter_increments_after_request() -> None:
    client = TestClient(app)

    _ = client.get("/health")
    metrics = client.get("/metrics")

    assert metrics.status_code == 200
    assert 'materials_api_requests_total{method="GET",path="/health",status="200"}' in metrics.text
