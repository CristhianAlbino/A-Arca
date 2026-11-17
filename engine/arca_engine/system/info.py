"""Real hardware numbers for the HOME screen: RAM, VRAM and disk.

VRAM comes from NVIDIA's NVML (package nvidia-ml-py) when installed, otherwise
from `nvidia-smi`. When neither is available the value is null together with a
reason: the interface shows "indisponível" instead of inventing a number.
"""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import psutil


def memory() -> dict[str, Any]:
    vm = psutil.virtual_memory()
    return {
        "total_bytes": vm.total,
        "available_bytes": vm.available,
        "used_bytes": vm.total - vm.available,
        "percent": round(vm.percent, 1),
    }


def disk(path: str | Path) -> dict[str, Any]:
    usage = shutil.disk_usage(path)
    return {
        "path": str(path),
        "total_bytes": usage.total,
        "used_bytes": usage.used,
        "free_bytes": usage.free,
        "percent": round(usage.used / usage.total * 100, 1) if usage.total else None,
    }


def _gpu_from_nvml() -> list[dict[str, Any]] | None:
    try:
        import pynvml  # provided by nvidia-ml-py
    except ImportError:
        return None
    try:
        pynvml.nvmlInit()
    except Exception:  # noqa: BLE001 - NVML raises its own error types
        return None
    try:
        gpus = []
        for i in range(pynvml.nvmlDeviceGetCount()):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
            name = pynvml.nvmlDeviceGetName(handle)
            gpus.append(
                {
                    "name": name.decode() if isinstance(name, bytes) else str(name),
                    "total_bytes": int(mem.total),
                    "used_bytes": int(mem.used),
                    "source": "nvml",
                }
            )
        return gpus
    finally:
        pynvml.nvmlShutdown()


def _gpu_from_nvidia_smi() -> list[dict[str, Any]] | None:
    exe = shutil.which("nvidia-smi")
    if not exe:
        return None
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform.startswith("win") else 0
    try:
        out = subprocess.run(
            [exe, "--query-gpu=name,memory.total,memory.used", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=3,
            creationflags=flags,
            check=True,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    return parse_nvidia_smi(out)


def parse_nvidia_smi(output: str) -> list[dict[str, Any]]:
    gpus = []
    for line in output.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) != 3:
            continue
        name, total_mib, used_mib = parts
        try:
            gpus.append(
                {
                    "name": name,
                    "total_bytes": int(float(total_mib) * 1024 * 1024),
                    "used_bytes": int(float(used_mib) * 1024 * 1024),
                    "source": "nvidia-smi",
                }
            )
        except ValueError:
            continue
    return gpus


def gpus() -> dict[str, Any]:
    for probe in (_gpu_from_nvml, _gpu_from_nvidia_smi):
        found = probe()
        if found:
            return {"available": True, "devices": found, "reason": None}
    return {
        "available": False,
        "devices": [],
        "reason": "Nenhuma GPU NVIDIA encontrada (NVML e nvidia-smi indisponíveis).",
    }


def snapshot(data_dir: Path) -> dict[str, Any]:
    return {
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python": platform.python_version(),
        },
        "cpu": {"logical_cores": psutil.cpu_count(logical=True), "percent": psutil.cpu_percent(None)},
        "memory": memory(),
        "gpu": gpus(),
        "data_disk": disk(data_dir),
    }
