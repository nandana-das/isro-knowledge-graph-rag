import json
import time

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.api.pipeline import GenerationUnavailable
from src.config.runtime import CORRECTED_RERUN_RESULTS_PATH as RESULTS


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("KG_RAG_MOCK_DELAY_MS", "0")
    with TestClient(create_app("mock")) as test_client:
        for _ in range(100):
            if test_client.get("/api/health").json()["status"] == "ready":
                break
            time.sleep(0.05)
        yield test_client


def _rerun_answer(question_id: str) -> tuple[str, str]:
    for line in RESULTS.read_text(encoding="utf8").splitlines():
        row = json.loads(line)
        if row["question_id"] == question_id and row["system"] == "A_CURRENT":
            return row["question"], row["answer"]
    raise KeyError(question_id)


def test_health_reports_mock_mode(client):
    body = client.get("/api/health").json()
    assert body["status"] == "ready" and body["mode"] == "mock"


def test_examples_are_unique_benchmark_questions(client):
    examples = client.get("/api/examples").json()["examples"]
    assert len(examples) == 51
    assert {"question", "mission", "category"} <= set(examples[0])


def test_ask_returns_answer_with_provenance(client):
    question, answer = _rerun_answer("rakg_005")
    body = client.post("/api/ask", json={"question": question}).json()
    assert body["answer"] == answer and body["mode"] == "mock"
    assert body["analysis"]["relations"] == ["HAS_PAYLOAD", "DEVELOPED_BY"]
    assert 0 < len(body["kg_paths"]) <= 10 <= body["kg_paths_total"]
    hop = body["kg_paths"][0]["hops"][0]
    assert hop["source"]["url"].startswith("https://") and hop["source"]["document_id"]


def test_unknown_question_gets_labelled_mock_answer(client):
    body = client.post("/api/ask", json={"question": "What does Gaganyaan aim to do?"}).json()
    assert body["answer"].startswith("[MOCK ANSWER]") or body["abstained"]


def test_invalid_question_is_rejected(client):
    assert client.post("/api/ask", json={"question": ""}).status_code == 422
    assert client.post("/api/ask", json={"question": "x" * 501}).status_code == 422


def test_cors_allows_local_dev_server(client):
    response = client.options(
        "/api/ask",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"},
    )
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_model_unavailable_returns_503(client, monkeypatch):
    def unavailable(question):
        raise GenerationUnavailable("Language model unavailable. Is Ollama running?")

    monkeypatch.setattr(client.app.state.pipeline, "answer", unavailable)
    response = client.post("/api/ask", json={"question": "Which launch vehicle launched AstroSat?"})
    assert response.status_code == 503 and "Ollama" in response.json()["detail"]


def test_not_ready_returns_503(client, monkeypatch):
    monkeypatch.setattr(client.app.state.pipeline, "status", "warming_up")
    assert client.post("/api/ask", json={"question": "Which launch vehicle launched AstroSat?"}).status_code == 503


def test_cors_allows_configured_site(monkeypatch):
    monkeypatch.setenv("KG_RAG_MOCK_DELAY_MS", "0")
    monkeypatch.setenv("KG_RAG_CORS_ORIGINS", "https://astra.example.app")
    with TestClient(create_app("mock")) as test_client:
        response = test_client.options(
            "/api/ask",
            headers={
                "Origin": "https://astra.example.app",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://astra.example.app"
    assert "content-type" in response.headers.get("access-control-allow-headers", "").lower()


def test_live_generation_retries_once_after_runner_error(monkeypatch):
    import src.api.pipeline as pipeline_module
    import src.generator.ollama_api as ollama_api
    import src.retriever.faiss_retriever as faiss_retriever

    calls = []

    def flaky_generate(question, context, options=None, system_prompt=None):
        calls.append(question)
        if len(calls) == 1:
            return "I don't know.", {"status": "error", "failure": "HTTPError"}
        return "PSLV-C30 (XL)", {"status": "ok", "prompt_tokens": 10, "context_tokens_used": 5, "context_trimmed": False}

    empty = {"retrieved_chunk_ids": [], "retrieved_chunk_scores": [], "retrieved_text": []}
    monkeypatch.setattr(pipeline_module, "retrieve_dense_chunks", lambda q: empty)
    monkeypatch.setattr(pipeline_module, "retrieve_bm25_chunks", lambda q: empty)
    monkeypatch.setattr(pipeline_module, "GENERATION_RETRY_DELAY_S", 0)
    monkeypatch.setattr(ollama_api, "generate_with_metrics", flaky_generate)
    monkeypatch.setattr(faiss_retriever, "_load_chunk_records", lambda: [])
    response = pipeline_module.LivePipeline().answer("Which launch vehicle launched AstroSat?")
    assert len(calls) == 2 and response.answer == "PSLV-C30 (XL)" and response.mode == "live"
