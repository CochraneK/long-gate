import pytest

from longgate.profiles import (
    get_profile,
    list_profiles,
    load_profile_file,
)


def test_all_builtin_profiles_keep_row_egress_closed():
    for profile in list_profiles():
        assert profile.row_level_synthetic_egress is False


def test_clinical_preset_is_more_conservative_than_research():
    research = get_profile("research")
    clinical = get_profile("clinical")
    assert clinical.min_dataset_size >= research.min_dataset_size
    assert clinical.min_group_size >= research.min_group_size
    assert clinical.rare_k >= research.rare_k
    assert (
        clinical.max_near_copy_rate
        <= research.max_near_copy_rate
    )


def test_unknown_profile_fails_closed():
    with pytest.raises(ValueError):
        get_profile("unknown")


def test_custom_profile_file_loads_stricter_policy(tmp_path):
    path = tmp_path / "org.json"
    path.write_text(
        """{
          "name": "org",
          "min_dataset_size": 40,
          "min_group_size": 12,
          "rare_k": 12,
          "max_near_copy_rate": 0.005,
          "row_level_synthetic_egress": false,
          "description": "Reviewed local policy."
        }""",
        encoding="utf-8",
    )
    profile = load_profile_file(path)
    assert profile.name == "org"
    assert profile.min_dataset_size == 40
    assert profile.row_level_synthetic_egress is False


def test_custom_profile_cannot_enable_row_level_egress(tmp_path):
    path = tmp_path / "unsafe.json"
    path.write_text(
        """{
          "name": "unsafe",
          "min_dataset_size": 10,
          "min_group_size": 5,
          "rare_k": 5,
          "max_near_copy_rate": 0.02,
          "row_level_synthetic_egress": true,
          "description": "Should fail closed."
        }""",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="cannot enable row-level"):
        load_profile_file(path)


def test_custom_profile_rejects_unknown_fields(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text(
        """{
          "name": "org",
          "min_dataset_size": 40,
          "min_group_size": 12,
          "rare_k": 12,
          "max_near_copy_rate": 0.005,
          "row_level_synthetic_egress": false,
          "description": "Reviewed local policy.",
          "magic_override": true
        }""",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="unknown fields"):
        load_profile_file(path)
