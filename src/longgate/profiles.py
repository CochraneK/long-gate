from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


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


def _profile_from_mapping(data: dict[str, object], source: str) -> PrivacyProfile:
    required = {
        "name",
        "min_dataset_size",
        "min_group_size",
        "rare_k",
        "max_near_copy_rate",
        "row_level_synthetic_egress",
        "description",
    }
    missing = required - data.keys()
    extra = data.keys() - required
    if missing:
        raise ValueError(
            f"Privacy profile {source} is missing fields: {sorted(missing)}"
        )
    if extra:
        raise ValueError(
            f"Privacy profile {source} has unknown fields: {sorted(extra)}"
        )

    name = data["name"]
    description = data["description"]
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Privacy profile name must be a non-empty string.")
    if not isinstance(description, str) or not description.strip():
        raise ValueError("Privacy profile description must be a non-empty string.")

    def positive_int(key: str, minimum: int = 2) -> int:
        value = data[key]
        if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
            raise ValueError(
                f"Privacy profile {key} must be an integer >= {minimum}."
            )
        return value

    max_near = data["max_near_copy_rate"]
    if (
        isinstance(max_near, bool)
        or not isinstance(max_near, (int, float))
        or not 0 <= float(max_near) <= 1
    ):
        raise ValueError(
            "Privacy profile max_near_copy_rate must be between 0 and 1."
        )

    row_level = data["row_level_synthetic_egress"]
    if not isinstance(row_level, bool):
        raise ValueError(
            "Privacy profile row_level_synthetic_egress must be boolean."
        )
    if row_level:
        raise ValueError(
            "Custom profiles cannot enable row-level synthetic egress in the "
            "pre-1.0 baseline. Keep it false and use the release ladder."
        )

    return PrivacyProfile(
        name=name.strip(),
        min_dataset_size=positive_int("min_dataset_size"),
        min_group_size=positive_int("min_group_size"),
        rare_k=positive_int("rare_k"),
        max_near_copy_rate=float(max_near),
        row_level_synthetic_egress=False,
        description=description.strip(),
    )


def load_profile_file(path: str | Path) -> PrivacyProfile:
    source = Path(path).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(source)
    if source.suffix.lower() != ".json":
        raise ValueError(
            "Custom privacy profiles currently use JSON only."
        )
    data = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Privacy profile file must contain a JSON object.")
    return _profile_from_mapping(data, str(source))


def resolve_profile(
    name: str = "research",
    profile_file: str | Path | None = None,
) -> PrivacyProfile:
    if profile_file is not None:
        return load_profile_file(profile_file)
    return get_profile(name)
