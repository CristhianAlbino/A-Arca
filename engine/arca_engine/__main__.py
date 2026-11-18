"""Start the engine.

    python -m arca_engine                 # random port, new token (how the app runs it)
    python -m arca_engine --port 8765 --token dev   # fixed values for browser development

On start it prints exactly one JSON line on stdout:
    {"event": "ready", "port": 54123, "token": "...", "version": "0.1.0.dev0"}
The Tauri shell reads that line to know where the engine is and how to call it.
Logs go to stderr and to the logs folder, never to stdout.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import socket
import sys
import threading

from . import __version__
from .config.paths import resolve_app_paths
from .context import AppContext
from .logging_setup import setup_logging
from .security.token import new_token

log = logging.getLogger("arca_engine")


def _exit_when_parent_closes_stdin() -> None:
    """When launched as a sidecar, a closed stdin means the window is gone: stop too."""

    def watch() -> None:
        try:
            while sys.stdin.read(1024):
                pass
        except (OSError, ValueError):
            pass
        log.info("stdin fechado pelo processo pai; encerrando o motor")
        os._exit(0)

    threading.Thread(target=watch, name="parent-watch", daemon=True).start()


REQUIRED_MODULES = ["fastapi", "uvicorn", "psutil", "libzim.reader", "libzim.search", "libzim.suggestion", "pypdf"]


def check_dependencies() -> int:
    """Import every runtime dependency; print one line each. Non-zero exit if any is missing."""
    import importlib

    missing = 0
    for name in REQUIRED_MODULES:
        try:
            importlib.import_module(name)
            print(f"ok       {name}")
        except ImportError as exc:
            missing += 1
            print(f"FALTANDO {name}: {exc}")
    return 1 if missing else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="arca-engine", description="Motor local da ARCA")
    parser.add_argument("--port", type=int, default=0, help="0 = porta livre aleatória")
    parser.add_argument("--token", default=None, help="Somente para desenvolvimento no navegador")
    parser.add_argument("--sidecar", action="store_true", help="Encerrar quando o app fechar")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument(
        "--check-deps", action="store_true", help="Conferir as bibliotecas do motor e sair (usado no build)"
    )
    args = parser.parse_args(argv)

    if args.check_deps:
        return check_dependencies()

    paths = resolve_app_paths().ensure()
    setup_logging(paths.logs_dir)
    token = args.token or new_token()
    ctx = AppContext.create(paths, token)

    import uvicorn  # imported late so --help and --version work without it

    from . import service
    from .api.app import create_app

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", args.port))  # loopback only, never 0.0.0.0
    sock.listen(128)
    port = sock.getsockname()[1]

    service.engine_started(ctx)
    log.info("ARCA Engine %s em 127.0.0.1:%s (dados em %s)", __version__, port, paths.data_dir)
    print(json.dumps({"event": "ready", "port": port, "token": token, "version": __version__}), flush=True)

    if args.sidecar:
        _exit_when_parent_closes_stdin()

    server = uvicorn.Server(uvicorn.Config(create_app(ctx), log_config=None, access_log=False))
    try:
        server.run(sockets=[sock])
    finally:
        ctx.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
