from fastapi.testclient import TestClient

from app.main import app


def test_query_success_without_debug(monkeypatch):
    def fake_query(question: str, question_type: str | None = None):
        return {
            "answer": "42",
            "refusal": False,
            "reason": "ok",
            "sources": [12],
            "gate": {"decision": "allow_answer"},
            "retrieval_debug": {"mode": "hybrid_rerank"},
        }

    monkeypatch.setattr("app.api.v1.rag.RagService.query", fake_query)

    c = TestClient(app)
    r = c.post("/v1/rag/query", json={"question": "test"})
    assert r.status_code == 200
    body = r.json()
    assert body["answer"] == "42"
    assert body["retrieval_debug"] is None


def test_query_success_with_debug(monkeypatch):
    def fake_query(question: str, question_type: str | None = None):
        return {
            "answer": "42",
            "refusal": False,
            "reason": "ok",
            "sources": [12],
            "gate": {"decision": "allow_answer"},
            "retrieval_debug": {"mode": "hybrid_rerank"},
        }

    monkeypatch.setattr("app.api.v1.rag.RagService.query", fake_query)

    c = TestClient(app)
    r = c.post("/v1/rag/query", json={"question": "test", "include_debug": True})
    assert r.status_code == 200
    body = r.json()
    assert body["retrieval_debug"] == {"mode": "hybrid_rerank"}


def test_index_success(monkeypatch):
    monkeypatch.setattr("app.api.v1.rag.RagService.build_index", lambda: 123)

    c = TestClient(app)
    r = c.post("/v1/rag/index")
    assert r.status_code == 200
    assert r.json()["chunks"] == 123
