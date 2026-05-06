"""
GPU detection module.

Detects NVIDIA GPUs via nvidia-smi.
Handles: Linux, Windows, WSL2 (driver is on Windows host).
Never raises — returns empty list if nvidia-smi is not available.
"""
from __future__ import annotations

import re
import subprocess
from typing import NamedTuple

from envforge_agent.schemas import GPUInfo


def detect_gpus() -> list[GPUInfo]:
    """
    Detect all NVIDIA GPUs using nvidia-smi.

    Returns an empty list (not an error) if:
    - nvidia-smi is not installed
    - No NVIDIA GPU is present
    - nvidia-smi fails for any reason (AMD GPU, etc.)
    """
    try:
        return _detect_via_nvidia_smi()
    except Exception:
        return []


def _detect_via_nvidia_smi() -> list[GPUInfo]:
    """
    Run nvidia-smi with CSV query and parse output.

    Queries: name, memory.total (MiB), driver_version, per GPU index.
    """
    result = subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=index,name,memory.total,driver_version",
            "--format=csv,noheader,nounits",
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )

    if result.returncode != 0:
        return []

    gpus: list[GPUInfo] = []
    for line in result.stdout.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 4:
            continue

        index_str, name, memory_mib_str, driver = parts[:4]

        try:
            index = int(index_str)
        except ValueError:
            index = len(gpus)

        vram_gb: float | None = None
        try:
            vram_mib = float(memory_mib_str)
            vram_gb = round(vram_mib / 1024, 2)
        except (ValueError, TypeError):
            pass

        gpus.append(
            GPUInfo(
                name=name,
                vram_gb=vram_gb,
                driver_version=driver if driver and driver != "[N/A]" else None,
                index=index,
            )
        )

    return gpus
