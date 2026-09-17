from __future__ import annotations

import os
import platform
import shutil
import subprocess  # nosec B404 - fixed local nvidia-smi probe; no user command input
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class GPUInfo:
    name: str
    vram_gb: float | None
    source: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class HardwareProfile:
    system: str
    release: str
    architecture: str
    processor: str
    logical_cpus: int | None
    ram_gb: float | None
    free_disk_gb: float | None
    disk_path: str
    gpus: list[GPUInfo]

    def to_dict(self) -> dict[str, object]:
        return {
            **asdict(self),
            "gpus": [gpu.to_dict() for gpu in self.gpus],
        }


def _windows_ram_gb() -> float | None:
    if platform.system() != "Windows":
        return None
    try:
        import ctypes

        class MemoryStatus(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        status = MemoryStatus()
        status.dwLength = ctypes.sizeof(MemoryStatus)
        ok = ctypes.windll.kernel32.GlobalMemoryStatusEx(  # type: ignore[attr-defined]
            ctypes.byref(status)
        )
        if not ok:
            return None
        return round(status.ullTotalPhys / (1024**3), 2)
    except (AttributeError, OSError, TypeError, ValueError):
        return None


def detect_system_ram_gb() -> float | None:
    windows = _windows_ram_gb()
    if windows is not None:
        return windows

    try:
        page_size = os.sysconf("SC_PAGE_SIZE")
        pages = os.sysconf("SC_PHYS_PAGES")
        return round((int(page_size) * int(pages)) / (1024**3), 2)
    except (AttributeError, OSError, TypeError, ValueError):
        return None


def detect_nvidia_gpus() -> list[GPUInfo]:
    binary = shutil.which("nvidia-smi")
    if not binary:
        return []
    try:
        result = subprocess.run(  # noqa: S603  # nosec B603 - fixed local query only
            [
                binary,
                "--query-gpu=name,memory.total",
                "--format=csv,noheader,nounits",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=3,
        )
    except (OSError, subprocess.SubprocessError):
        return []

    gpus: list[GPUInfo] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        name, separator, raw_memory = line.rpartition(",")
        if not separator:
            continue
        try:
            vram_gb = round(float(raw_memory.strip()) / 1024, 2)
        except ValueError:
            vram_gb = None
        gpus.append(
            GPUInfo(
                name=name.strip(),
                vram_gb=vram_gb,
                source="nvidia-smi",
            )
        )
    return gpus


def detect_hardware(
    disk_path: str | Path | None = None,
    *,
    ram_gb: float | None = None,
) -> HardwareProfile:
    root = Path(disk_path or Path.home()).expanduser().resolve()
    try:
        free_disk_gb = round(shutil.disk_usage(root).free / 1_000_000_000, 2)
    except OSError:
        free_disk_gb = None

    return HardwareProfile(
        system=platform.system() or "unknown",
        release=platform.release() or "unknown",
        architecture=platform.machine() or "unknown",
        processor=platform.processor() or "unknown",
        logical_cpus=os.cpu_count(),
        ram_gb=(float(ram_gb) if ram_gb is not None else detect_system_ram_gb()),
        free_disk_gb=free_disk_gb,
        disk_path=str(root),
        gpus=detect_nvidia_gpus(),
    )
