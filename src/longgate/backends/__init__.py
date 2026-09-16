from .base import SyntheticBackend
from .demo import DemoBackend
from .mostlyai import MostlyAIBackend
from .synthcity import SynthCityBackend


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
    "DemoBackend",
    "MostlyAIBackend",
    "SynthCityBackend",
    "SyntheticBackend",
    "get_backend",
]
