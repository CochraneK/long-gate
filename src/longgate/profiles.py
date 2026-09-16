from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class PrivacyProfile:
    """Engineering defaults, not legal/compliance certifications."""

    name: str
    min_dataset_size: int
    min_group_size: int
    rare_k: int
    max_near_copy_rate: float
    row_level_synthetic_egress: bool
    description: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


_PROFILES = {
    "research": PrivacyProfile(
        name="research",
        min_dataset_size=10,
        min_group_size=5,
        rare_k=5,
        max_near_copy_rate=0.02,
        row_level_synthetic_egress=False,
        description=(
            "Conservative research default. Suitable as a starting point for "
            "development and reproducible analysis, not as a privacy guarantee."
        ),
    ),
    "clinical": PrivacyProfile(
        name="clinical",
        min_dataset_size=30,
        min_group_size=10,
        rare_k=10,
        max_near_copy_rate=0.01,
        row_level_synthetic_egress=False,
        description=(
            "Higher-sensitivity engineering preset. The name does not imply "
            "HIPAA, GDPR, NHS, medical-device, or other compliance certification."
        ),
    ),
    "enterprise": PrivacyProfile(
        name="enterprise",
        min_dataset_size=20,
        min_group_size=10,
        rare_k=10,
        max_near_copy_rate=0.015,
        row_level_synthetic_egress=False,
        description=(
            "Conservative organizational-data preset. Organizations should "
            "replace these defaults with reviewed internal policy."
        ),
    ),
}


def list_profiles() -> list[PrivacyProfile]:
    return list(_PROFILES.values())


def get_profile(name: str) -> PrivacyProfile:
    key = name.strip().lower()
    try:
        return _PROFILES[key]
    except KeyError as exc:
        raise ValueError(
            f"Unknown privacy profile: {name!r}. "
            f"Available: {', '.join(sorted(_PROFILES))}"
        ) from exc
