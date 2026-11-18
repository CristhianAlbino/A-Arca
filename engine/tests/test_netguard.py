import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from arca_engine.netguard import NetGuard, NetPolicy, NetworkBlocked


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/redirect-out":
            self.send_response(302)
            self.send_header("Location", "https://example.com/roubado")
            self.end_headers()
            return
        body = b"ok-local"
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


@pytest.fixture
def local_server():
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


def guard(mode="blocked", allow=(), blocked_log=None):
    policy = NetPolicy(mode=mode, allowlist=frozenset(allow))
    return NetGuard(lambda: policy, on_blocked=blocked_log.append if blocked_log is not None else None)


def test_loopback_is_always_allowed(local_server):
    g = guard()
    resp = g.get(local_server + "/")
    assert resp.status == 200 and resp.body == b"ok-local"


def test_external_is_blocked_by_default():
    log = []
    g = guard(blocked_log=log)
    with pytest.raises(NetworkBlocked) as err:
        g.get("https://example.com/?chave=secreta")
    assert err.value.reason == "modo offline"
    assert log and log[0]["host"] == "example.com"
    assert "secreta" not in log[0]["url"]  # query strings never logged


def test_online_still_requires_allowlist():
    g = guard(mode="online", allow={"api.anthropic.com"})
    with pytest.raises(NetworkBlocked):
        g.check("https://example.com/")
    g.check("https://api.anthropic.com/v1/messages")  # allowed, no exception


def test_wildcard_allowlist():
    g = guard(mode="online", allow={"*.googleapis.com"})
    g.check("https://generativelanguage.googleapis.com/")
    with pytest.raises(NetworkBlocked):
        g.check("https://googleapis.com.evil.net/")


def test_only_http_schemes():
    with pytest.raises(NetworkBlocked):
        guard(mode="online", allow={"example.com"}).check("ftp://example.com/")


def test_redirect_to_blocked_host_is_stopped(local_server):
    g = guard()
    with pytest.raises(NetworkBlocked):
        g.get(local_server + "/redirect-out")
    blocked = g.attempts(only_blocked=True)
    assert blocked[0]["host"] == "example.com"


def test_attempts_history_newest_first(local_server):
    g = guard()
    g.get(local_server + "/a")
    with pytest.raises(NetworkBlocked):
        g.check("https://example.org/")
    history = g.attempts()
    assert history[0]["host"] == "example.org" and history[0]["allowed"] is False
    assert history[1]["allowed"] is True
