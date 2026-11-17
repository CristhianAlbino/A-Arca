"""UI smoke test: builds the preview, starts the preview server, drives Chromium.

Run from the repository root:
    NODE_PATH=<folder with esbuild, react, react-dom> python -m pytest tests/e2e -q

Checks: HOME renders real numbers, registering a volume works through the form,
sections that are not built say so, and the page makes no request outside 127.0.0.1.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

playwright = pytest.importorskip("playwright.sync_api")

ROOT = Path(__file__).resolve().parents[2]
TOKEN = "token-e2e-" + "z" * 30
SHOTS = Path(os.environ.get("ARCA_SCREENSHOTS", "/tmp/arca-shots"))


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def app_url(tmp_path_factory):
    port = _free_port()
    ui_dir = tmp_path_factory.mktemp("ui")
    url = f"http://127.0.0.1:{port}"
    subprocess.run(
        ["node", str(ROOT / "scripts/ui-preview/build.mjs"), str(ui_dir), url, TOKEN],
        check=True,
        capture_output=True,
    )
    env = {**os.environ, "ARCA_HOME": str(tmp_path_factory.mktemp("arca-home"))}
    proc = subprocess.Popen(
        [sys.executable, str(ROOT / "scripts/ui-preview/server.py"), str(ui_dir), str(port), TOKEN], env=env
    )
    for _ in range(50):
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
            break
        except OSError:
            time.sleep(0.1)
    yield url
    proc.terminate()
    proc.wait(timeout=5)


def test_home_volume_and_placeholders(app_url, tmp_path):
    SHOTS.mkdir(parents=True, exist_ok=True)
    external, errors = [], []
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.on("request", lambda r: None if r.url.startswith("http://127.0.0.1") else external.append(r.url))
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(app_url)

        page.get_by_role("heading", name="Seu acervo começa aqui").wait_for()
        assert page.get_by_role("meter", name="RAM").count() == 1
        assert "OFFLINE" in page.locator(".topbar").inner_text()
        page.screenshot(path=str(SHOTS / "01-inicio.png"), full_page=True)

        ssd = tmp_path / "SSD-teste"
        ssd.mkdir()
        page.get_by_role("button", name="Adicionar volume").click()
        page.get_by_label("Pasta do volume").fill(str(ssd))
        page.get_by_label("Nome").fill("ARCA-TESTE")
        page.get_by_role("button", name="Registrar").click()
        page.get_by_role("heading", name="ARCA-TESTE").wait_for()
        assert (ssd / ".arca-volume.json").exists()
        page.get_by_text("Volume registrado: ARCA-TESTE").wait_for(timeout=7000)
        page.screenshot(path=str(SHOTS / "02-volume-registrado.png"), full_page=True)

        page.get_by_role("navigation", name="Principal").get_by_role("button", name="Conhecimento").click()
        page.get_by_text("CHEGA NA FASE 3").wait_for()
        page.get_by_role("navigation", name="Principal").get_by_role("button", name="Entretenimento").click()
        page.get_by_text("CHEGA NA FASE 6").wait_for()
        page.screenshot(path=str(SHOTS / "03-entretenimento.png"))
        browser.close()

    assert errors == [], errors
    assert external == [], f"Requisições para fora do computador: {external}"


@pytest.fixture(scope="module")
def chat_app_url(tmp_path_factory):
    sys.path.insert(0, str(ROOT / "engine"))
    from tests.fakes.fake_ollama import FakeOllama

    fake = FakeOllama(token_delay=0.03)
    ollama_url = fake.start()
    port = _free_port()
    ui_dir = tmp_path_factory.mktemp("ui-chat")
    url = f"http://127.0.0.1:{port}"
    subprocess.run(
        ["node", str(ROOT / "scripts/ui-preview/build.mjs"), str(ui_dir), url, TOKEN], check=True, capture_output=True
    )
    env = {**os.environ, "ARCA_HOME": str(tmp_path_factory.mktemp("arca-home-chat"))}
    proc = subprocess.Popen(
        [sys.executable, str(ROOT / "scripts/ui-preview/server.py"), str(ui_dir), str(port), TOKEN, ollama_url],
        env=env,
    )
    for _ in range(50):
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
            break
        except OSError:
            time.sleep(0.1)
    yield url
    proc.terminate()
    proc.wait(timeout=5)
    fake.stop()


def test_chat_with_local_model(chat_app_url):
    SHOTS.mkdir(parents=True, exist_ok=True)
    external, errors = [], []
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.on("request", lambda r: None if r.url.startswith("http://127.0.0.1") else external.append(r.url))
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(chat_app_url)
        page.get_by_role("navigation", name="Principal").get_by_role("button", name="IA", exact=True).click()
        page.get_by_role("heading", name="Como posso ajudar?").wait_for()

        page.get_by_label("Modelo").select_option("teste-pequeno:3b")
        box = page.get_by_label("Mensagem para a ARCA")
        box.fill("Qual é a capital do Brasil?")
        box.press("Enter")
        page.get_by_text("[Ollama de teste] Você disse: Qual é a capital do Brasil?").wait_for()
        page.get_by_text("tokens/s").wait_for()
        history = page.get_by_role("navigation", name="Histórico")
        history.get_by_role("button", name="Qual é a capital do Brasil?", exact=True).wait_for()
        page.screenshot(path=str(SHOTS / "04-conversa.png"))

        # A model that does not fit is refused with an explanation, nothing is invented.
        page.get_by_label("Modelo").select_option("teste-gigante:70b")
        box.fill("teste de memória")
        box.press("Enter")
        page.get_by_text("Escolha um modelo menor").wait_for()
        page.screenshot(path=str(SHOTS / "05-modelo-grande-recusado.png"))

        # New conversation, then reopen the first one from the sidebar.
        page.get_by_role("button", name="Nova conversa").click()
        page.get_by_role("heading", name="Como posso ajudar?").wait_for()
        history.get_by_role("button", name="Qual é a capital do Brasil?", exact=True).click()
        page.get_by_text("[Ollama de teste] Você disse: Qual é a capital do Brasil?").wait_for()
        browser.close()

    assert errors == [], errors
    assert external == [], f"Requisições para fora do computador: {external}"
