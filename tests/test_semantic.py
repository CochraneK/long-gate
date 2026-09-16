from pathlib import Path

import pytest

from longgate.semantic import (
    LocalLlamaCppTransformer,
    audit_semantic_preview,
)


def test_semantic_preview_detects_direct_pii():
    audit = audit_semantic_preview(
        "The participant can be contacted later.",
        "Email person@example.com for details.",
    )
    assert audit.direct_pii_hits >= 1
    assert audit.release_allowed is False


def test_semantic_preview_detects_long_exact_reuse():
    source = (
        "This is a deliberately long sentence about a participant "
        "and their experience in a highly specific research setting."
    )
    audit = audit_semantic_preview(
        source,
        source,
        character_ngram_size=16,
    )
    assert (
        audit.character_ngram_reuse_rate
        > 0.9
    )
    assert audit.release_allowed is False


def test_semantic_preview_detects_reused_numbers():
    audit = audit_semantic_preview(
        "The event occurred on 2026-09-16 and code 12345.",
        "An event occurred on 2026-09-16.",
    )
    assert audit.reused_number_tokens >= 1


def test_local_transformer_requires_existing_model(
    tmp_path: Path,
):
    with pytest.raises(FileNotFoundError):
        LocalLlamaCppTransformer(
            tmp_path / "missing.gguf"
        )
