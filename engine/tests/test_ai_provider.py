import pytest

from arca_engine.ai.base import ChatMessage, ProviderError
from arca_engine.ai.budget import GB, check_fit
from arca_engine.ai.ollama import OllamaProvider
from arca_engine.netguard import NetGuard, NetPolicy, NetworkBlocked
from tests.fakes.fake_ollama import FakeOllama


@pytest.fixture
def fake():
    f = FakeOllama(token_delay=0)
    yield f
    f.stop()


def guard():
    return NetGuard(lambda: NetPolicy())  # blocked mode: only loopback


def test_status_models_and_chat_stream(fake):
    url = fake.start()
    ollama = OllamaProvider(guard(), url)
    assert ollama.status() == {"available": True, "version": "0.0.0-fake", "reason": None}
    names = [m.name for m in ollama.list_models()]
    assert "teste-padrao:8b" in names

    chunks = list(ollama.chat("teste-padrao:8b", [ChatMessage("user", "olá ARCA")]))
    text = "".join(c.text for c in chunks)
    assert text == "[Ollama de teste] Você disse: olá ARCA"
    assert chunks[-1].done and chunks[-1].stats["output_tokens"] == 7
    assert chunks[-1].stats["tokens_per_second"] == 7.0
    assert [m.name for m in ollama.loaded()] == ["teste-padrao:8b"]

    ollama.unload("teste-padrao:8b")
    assert ollama.loaded() == []


def test_missing_model_is_a_provider_error(fake):
    ollama = OllamaProvider(guard(), fake.start())
    with pytest.raises(ProviderError, match="not found"):
        list(ollama.chat("nao-existe", [ChatMessage("user", "oi")]))


def test_ollama_not_running_is_reported_not_raised():
    status = OllamaProvider(guard(), "http://127.0.0.1:9").status()  # nothing listens on port 9
    assert status["available"] is False
    assert "Ollama" in status["reason"]


def test_remote_ollama_needs_permission():
    ollama = OllamaProvider(guard(), "http://192.168.0.50:11434")
    with pytest.raises(NetworkBlocked):
        ollama.list_models()


def test_budget():
    assert check_fit(int(4.9 * GB), vram_free_bytes=int(7.5 * GB), ram_free_bytes=12 * GB).mode == "gpu"
    partial = check_fit(int(9 * GB), vram_free_bytes=int(7.5 * GB), ram_free_bytes=12 * GB)
    assert partial.ok and partial.mode == "partial"
    refused = check_fit(40 * GB, vram_free_bytes=int(7.5 * GB), ram_free_bytes=12 * GB)
    assert not refused.ok and "menor" in refused.message
    assert check_fit(2 * GB, vram_free_bytes=None, ram_free_bytes=8 * GB).mode == "cpu"
    assert not check_fit(9 * GB, vram_free_bytes=None, ram_free_bytes=8 * GB).ok


def test_chat_asks_for_answer_without_hidden_thinking(fake):
    ollama = OllamaProvider(guard(), fake.start())
    list(ollama.chat("teste-pequeno:3b", [ChatMessage("user", "oi")]))
    body = next(b for method, path, b in fake.requests if path == "/api/chat")
    assert body["think"] is False


def test_chat_retries_without_think_when_refused(fake):
    fake.reject_think = True
    ollama = OllamaProvider(guard(), fake.start())
    chunks = list(ollama.chat("teste-pequeno:3b", [ChatMessage("user", "oi")]))
    assert chunks[-1].done and "Você disse: oi" in "".join(c.text for c in chunks)
    bodies = [b for method, path, b in fake.requests if path == "/api/chat"]
    assert "think" in bodies[0] and "think" not in bodies[1]
