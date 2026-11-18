import pytest

from arca_engine import service
from arca_engine.ai.budget import GB
from arca_engine.context import AppContext
from tests.fakes.fake_ollama import FakeOllama

PLENTY = lambda: (int(7.5 * GB), 12 * GB)


@pytest.fixture
def fake():
    f = FakeOllama(token_delay=0)
    yield f
    f.stop()


@pytest.fixture
def ctx(app_paths, fake):
    c = AppContext.create(app_paths, token="t" * 43, include_drive_roots=False)
    c.update_settings({"ollama_url": fake.start()})
    yield c
    c.close()


def run(ctx, text, model="teste-padrao:8b", conversation_id=None, probe=PLENTY):
    return list(service.chat(ctx, text, model, conversation_id, memory_probe=probe))


def test_status_lists_models(ctx):
    st = service.ai_status(ctx)
    assert st["available"] and st["version"] == "0.0.0-fake"
    assert {m["name"] for m in st["models"]} >= {"teste-padrao:8b", "teste-pequeno:3b"}


def test_chat_streams_and_saves(ctx):
    events = run(ctx, "Qual é a capital do Brasil?")
    kinds = [e["type"] for e in events]
    assert kinds[0] == "meta" and kinds[-1] == "done" and "delta" in kinds
    answer = "".join(e["text"] for e in events if e["type"] == "delta")
    assert answer.endswith("Qual é a capital do Brasil?")

    conv_id = events[0]["conversation_id"]
    conv = service.get_conversation(ctx, conv_id)
    assert conv["title"] == "Qual é a capital do Brasil?"
    assert [m["role"] for m in conv["messages"]] == ["user", "assistant"]
    assert conv["messages"][1]["content"] == answer
    assert conv["messages"][1]["stats"]["output_tokens"] > 0
    assert service.list_conversations(ctx)[0]["id"] == conv_id


def test_follow_up_sends_history_and_system_prompt(ctx, fake):
    first = run(ctx, "primeira pergunta")
    run(ctx, "segunda pergunta", conversation_id=first[0]["conversation_id"])
    sent = [b for (m, p, b) in fake.requests if p == "/api/chat"][-1]["messages"]
    assert sent[0]["role"] == "system" and "ARCA" in sent[0]["content"]
    assert [m["content"] for m in sent[1:] if m["role"] == "user"] == ["primeira pergunta", "segunda pergunta"]


def test_only_one_model_loaded_at_a_time(ctx, fake):
    run(ctx, "oi", model="teste-pequeno:3b")
    assert fake.loaded == "teste-pequeno:3b"
    run(ctx, "oi de novo", model="teste-padrao:8b")
    unloads = [b["model"] for (m, p, b) in fake.requests if p == "/api/generate"]
    assert unloads == ["teste-pequeno:3b"]
    assert fake.loaded == "teste-padrao:8b"


def test_model_too_big_is_refused_and_nothing_saved(ctx):
    events = run(ctx, "oi", model="teste-gigante:70b")
    assert events == [{"type": "error", "message": events[0]["message"]}]
    assert "menor" in events[0]["message"]
    assert service.list_conversations(ctx) == []


def test_partial_offload_warns(ctx):
    events = run(ctx, "oi", probe=lambda: (int(2 * GB), 12 * GB))
    assert events[0]["type"] == "notice" and "RAM" in events[0]["message"]
    assert events[-1]["type"] == "done"


def test_missing_model_and_empty_text(ctx):
    assert run(ctx, "oi", model="nao-existe")[0]["type"] == "error"
    assert run(ctx, "   ")[0] == {"type": "error", "message": "Escreva uma mensagem."}
    assert run(ctx, "oi", model=None)[0]["message"] == "Escolha um modelo para conversar."


def test_ollama_closed_gives_clear_error(ctx, fake):
    fake.stop()
    [event] = run(ctx, "oi")
    assert event["type"] == "error" and "Ollama" in event["message"]
    assert service.ai_status(ctx)["available"] is False


def test_stopping_mid_answer_keeps_partial_text(ctx):
    stream = service.chat(ctx, "uma resposta longa", "teste-padrao:8b", memory_probe=PLENTY)
    meta = next(stream)
    next(stream)  # first word arrived
    stream.close()  # the user pressed "parar"
    conv = service.get_conversation(ctx, meta["conversation_id"])
    last = conv["messages"][-1]
    assert last["role"] == "assistant" and last["status"] == "interrupted" and last["content"]


def test_delete_conversation(ctx):
    conv_id = run(ctx, "apagar depois")[0]["conversation_id"]
    service.delete_conversation(ctx, conv_id)
    with pytest.raises(service.ServiceError):
        service.get_conversation(ctx, conv_id)
