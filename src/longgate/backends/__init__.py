from .base import SyntheticBackend
from .demo import DemoBackend
from .synthcity import SynthCityBackend
from .mostlyai import MostlyAIBackend


def get_backend(name: str) -> SyntheticBackend:
    if name == "demo":
        return DemoBackend()
    if name == "synthcity":
        return SynthCityBackend()
    if name.startswith("synthcity:"):
        return SynthCityBackend(plugin=name.split(":", 1)[1])
    if name == "mostlyai":
        return MostlyAIBackend()
    raise ValueError(f"Unknown backend: {name}")


__all__ = [
    "SyntheticBackend",
    "DemoBackend",
    "SynthCityBackend",
    "MostlyAIBackend",
    "get_backend",
]
