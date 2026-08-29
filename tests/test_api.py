from types import SimpleNamespace

from fastapi.testclient import TestClient

import app.main as main


client = TestClient(main.app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_analyze_indexes_before_pipeline(monkeypatch):
    record = SimpleNamespace(
        qualified_name="sample_repo/orders.py::checkout",
        name="checkout",
        source="def checkout():\n    return 1",
        docstring="",
    )
    monkeypatch.setattr(main, "_index", lambda _: [record])

    class FakePipeline:
        def invoke(self, state):
            assert state["target_function"]["name"] == "checkout"
            return {
                "review": {"risk_flag": "low"},
                "graph_context": {"fan_in": 0, "fan_out": 0},
                "similar_functions": [],
            }

    monkeypatch.setattr(main, "pipeline", FakePipeline())

    r = client.post("/analyze", json={"repo_path": "sample_repo"})
    assert r.status_code == 200
    assert r.json()["results"][0]["function"].endswith("::checkout")


def test_analyze_unknown_function_returns_404(monkeypatch):
    record = SimpleNamespace(
        qualified_name="sample_repo/orders.py::checkout",
        name="checkout",
        source="def checkout():\n    return 1",
        docstring="",
    )
    monkeypatch.setattr(main, "_index", lambda _: [record])

    r = client.post(
        "/analyze",
        json={"repo_path": "sample_repo", "function_name": "missing"},
    )
    assert r.status_code == 404
