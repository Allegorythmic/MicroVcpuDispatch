from __future__ import annotations

from fastapi.testclient import TestClient

from workflow_orchestrator.dispatcher.app import app


def test_metrics_endpoint():
    client = TestClient(app)
    resp = client.get("/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert "queued" in data and "running" in data
