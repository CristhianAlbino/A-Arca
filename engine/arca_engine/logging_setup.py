from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(logs_dir: Path, level: int = logging.INFO) -> None:
    logs_dir.mkdir(parents=True, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    file_handler = RotatingFileHandler(
        logs_dir / "engine.log", maxBytes=2 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(fmt)
    stderr = logging.StreamHandler(sys.stderr)  # stdout is reserved for the ready line
    stderr.setFormatter(fmt)
    root = logging.getLogger()
    root.handlers[:] = [file_handler, stderr]
    root.setLevel(level)
