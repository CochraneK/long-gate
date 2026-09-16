from __future__ import annotations

import re
import unicodedata
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

from .documents import extract_document_text
from .model_vault import resolve_model_path
from .pii import scan_text
from .utils import write_json

_NUMBER_CANDIDATE_RE = re.compile(r"(?<!\w)\d[\d./:-]*")
_WORD_RE = re.compile(r"[^\W\d_][\w'-]{7,}", re.UNICODE)

SEMANTIC_MAX_NGRAM_REUSE_RATE = 0.01
SEMANTIC_MAX_DISTINCTIVE_TOKEN_REUSE_RATE = 0.05
SEMANTIC_MIN_OUTPUT_CHARACTERS = 80


def _number_tokens(text: str) -> set[str]:
    """Extract numeric/date-like tokens while ignoring trailing punctuation."""
    tokens: set[str] = set()
    for match in _NUMBER_CANDIDATE_RE.findall(text):
        normalized = match.rstrip("./:-")
        if normalized:
            tokens.add(normalized)
    return tokens


@dataclass(frozen=True)
class SemanticReleaseEvidence:
    criteria_version: str
    direct_pii_max: int
    reused_number_tokens_max: int
    max_character_ngram_reuse_rate: float
    max_distinctive_token_reuse_rate: float
    min_output_characters: int
    failed_conditions: list[str]
    eligible_for_manual_review: bool
    manual_review_required: bool
    automatic_release_allowed: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class SemanticPreviewAudit:
    direct_pii_hits: int
    pii_by_entity: dict[str, int]
    reused_number_tokens: int
    character_ngram_size: int
    reused_character_ngrams: int
    transformed_character_ngrams: int
    character_ngram_reuse_rate: float
    distinctive_source_tokens: int
    reused_distinctive_tokens: int
    distinctive_token_reuse_rate: float
    transformed_characters: int
    release_evidence: SemanticReleaseEvidence
    release_allowed: bool
    reasons: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class SemanticPreviewResult:
    output_path: str
    audit_path: str
    model_path: str
    release_allowed: bool
    note: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _normalized_characters(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).lower()
    return "".join(character for character in normalized if character.isalnum())


def _normalized_words(text: str) -> list[str]:
    normalized = unicodedata.normalize("NFKC", text).lower()
    return _WORD_RE.findall(normalized)


def _distinctive_token_stats(
    source: str,
    transformed: str,
) -> tuple[int, int, float]:
    source_counts = Counter(_normalized_words(source))
    distinctive = {
        token
        for token, count in source_counts.items()
        if count == 1
    }
    if not distinctive:
        return 0, 0, 0.0
    transformed_tokens = set(_normalized_words(transformed))
    reused = distinctive & transformed_tokens
    return (
        len(distinctive),
        len(reused),
        round(len(reused) / len(distinctive), 6),
    )


def _character_ngram_stats(
    source: str,
    transformed: str,
    size: int,
) -> tuple[int, int, float]:
    if size < 8:
        raise ValueError("Character n-gram size must be at least 8.")

    source_text = _normalized_characters(source)
    transformed_text = _normalized_characters(transformed)

    source_ngrams = {
        source_text[index : index + size]
        for index in range(max(0, len(source_text) - size + 1))
    }
    transformed_ngrams = [
        transformed_text[index : index + size]
        for index in range(max(0, len(transformed_text) - size + 1))
    ]

    reused = sum(1 for ngram in transformed_ngrams if ngram in source_ngrams)
    total = len(transformed_ngrams)
    rate = reused / total if total else 0.0
    return reused, total, round(rate, 6)


def evaluate_semantic_release_evidence(
    *,
    direct_pii_hits: int,
    reused_number_tokens: int,
    character_ngram_reuse_rate: float,
    distinctive_token_reuse_rate: float,
    transformed_characters: int,
) -> SemanticReleaseEvidence:
    """Evaluate a conservative evidence gate without enabling automatic release.

    Passing this gate means only that the defined mechanical checks are quiet
    enough for human/policy review. It is not an anonymity guarantee.
    """
    failures: list[str] = []
    if direct_pii_hits > 0:
        failures.append("direct_pii_detected")
    if reused_number_tokens > 0:
        failures.append("source_number_reuse")
    if character_ngram_reuse_rate > SEMANTIC_MAX_NGRAM_REUSE_RATE:
        failures.append("character_ngram_reuse")
    if distinctive_token_reuse_rate > SEMANTIC_MAX_DISTINCTIVE_TOKEN_REUSE_RATE:
        failures.append("distinctive_token_reuse")
    if transformed_characters < SEMANTIC_MIN_OUTPUT_CHARACTERS:
        failures.append("output_too_short")

    return SemanticReleaseEvidence(
        criteria_version="semantic-release-evidence-v1",
        direct_pii_max=0,
        reused_number_tokens_max=0,
        max_character_ngram_reuse_rate=SEMANTIC_MAX_NGRAM_REUSE_RATE,
        max_distinctive_token_reuse_rate=(
            SEMANTIC_MAX_DISTINCTIVE_TOKEN_REUSE_RATE
        ),
        min_output_characters=SEMANTIC_MIN_OUTPUT_CHARACTERS,
        failed_conditions=failures,
        eligible_for_manual_review=not failures,
        manual_review_required=True,
        automatic_release_allowed=False,
    )


def audit_semantic_preview(
    source: str,
    transformed: str,
    character_ngram_size: int = 32,
) -> SemanticPreviewAudit:
    pii = scan_text(transformed)

    source_numbers = _number_tokens(source)
    transformed_numbers = _number_tokens(transformed)
    reused_numbers = len(source_numbers & transformed_numbers)

    reused_ngrams, total_ngrams, reuse_rate = _character_ngram_stats(
        source,
        transformed,
        character_ngram_size,
    )
    (
        distinctive_source_tokens,
        reused_distinctive_tokens,
        distinctive_token_reuse_rate,
    ) = _distinctive_token_stats(source, transformed)

    release_evidence = evaluate_semantic_release_evidence(
        direct_pii_hits=pii.total_hits,
        reused_number_tokens=reused_numbers,
        character_ngram_reuse_rate=reuse_rate,
        distinctive_token_reuse_rate=distinctive_token_reuse_rate,
        transformed_characters=len(transformed),
    )

    reasons = [
        (
            "Semantic output remains local-only. Passing the engineering "
            "evidence gate is not proof of anonymity and never auto-enables egress."
        )
    ]
    if pii.total_hits:
        reasons.append(
            f"Detected {pii.total_hits} direct-PII pattern hit(s) in transformed text."
        )
    if reused_numbers:
        reasons.append(
            f"Detected {reused_numbers} exact numeric token(s) reused from the source."
        )
    if reuse_rate > SEMANTIC_MAX_NGRAM_REUSE_RATE:
        reasons.append(
            f"Character n-gram reuse rate {reuse_rate:.2%} exceeds the "
            f"{SEMANTIC_MAX_NGRAM_REUSE_RATE:.0%} manual-review threshold."
        )
    if distinctive_token_reuse_rate > SEMANTIC_MAX_DISTINCTIVE_TOKEN_REUSE_RATE:
        reasons.append(
            "Distinctive long-token reuse exceeds the manual-review threshold."
        )
    if release_evidence.eligible_for_manual_review:
        reasons.append(
            "Mechanical release-evidence checks passed; explicit human/policy "
            "review is still required and automatic release remains disabled."
        )

    return SemanticPreviewAudit(
        direct_pii_hits=pii.total_hits,
        pii_by_entity=pii.by_entity,
        reused_number_tokens=reused_numbers,
        character_ngram_size=character_ngram_size,
        reused_character_ngrams=reused_ngrams,
        transformed_character_ngrams=total_ngrams,
        character_ngram_reuse_rate=reuse_rate,
        distinctive_source_tokens=distinctive_source_tokens,
        reused_distinctive_tokens=reused_distinctive_tokens,
        distinctive_token_reuse_rate=distinctive_token_reuse_rate,
        transformed_characters=len(transformed),
        release_evidence=release_evidence,
        release_allowed=False,
        reasons=reasons,
    )


class LocalLlamaCppTransformer:
    """In-process local GGUF transformer.

    Private processing never downloads models and does not accept a remote
    endpoint. Models may be provisioned separately into the local Model Vault
    during network-enabled setup mode.
    """

    def __init__(
        self,
        model_path: str | Path,
        n_ctx: int = 4096,
        max_input_characters: int = 12000,
    ) -> None:
        self.model_path = resolve_model_path(model_path)
        self.n_ctx = n_ctx
        self.max_input_characters = max_input_characters

    def transform(
        self,
        text: str,
        max_tokens: int = 512,
    ) -> str:
        if len(text) > self.max_input_characters:
            raise ValueError(
                "Document is too long for the current single-pass semantic "
                "preview. Chunking is intentionally not performed silently."
            )

        try:
            from llama_cpp import Llama
        except ImportError as exc:
            raise RuntimeError(
                "Local semantic preview requires: "
                "pip install 'long-gate[local-llm]'"
            ) from exc

        model = Llama(
            model_path=str(self.model_path),
            n_ctx=self.n_ctx,
            verbose=False,
        )

        prompt = (
            "You are a LOCAL privacy transformation engine.\n"
            "Rewrite the source into an identity-detached abstract summary.\n"
            "Do not preserve names, contact details, exact addresses, "
            "exact dates, exact ages, exact identifiers, or rare organization "
            "names. Generalize unique combinations of events or roles when "
            "possible. Do not invent new identifying details.\n"
            "Return only the transformed narrative.\n\n"
            "SOURCE:\n"
            + text
            + "\n\nTRANSFORMED:\n"
        )
        response = model(
            prompt,
            max_tokens=max_tokens,
            temperature=0.1,
            echo=False,
        )
        choices = response.get("choices", [])
        if not choices:
            raise RuntimeError("Local llama.cpp model returned no completion.")

        transformed = str(choices[0].get("text", "")).strip()
        if not transformed:
            raise RuntimeError("Local llama.cpp model returned empty text.")
        return transformed


def semantic_transform_local(
    input_path: str | Path,
    model_path: str | Path,
    output_path: str | Path,
    max_tokens: int = 512,
) -> SemanticPreviewResult:
    source, _, _, _ = extract_document_text(input_path)

    transformer = LocalLlamaCppTransformer(model_path)
    transformed = transformer.transform(source, max_tokens=max_tokens)
    audit = audit_semantic_preview(source, transformed)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(transformed, encoding="utf-8")

    audit_path = output.with_name(output.name + ".audit.json")
    write_json(audit_path, audit.to_dict())

    return SemanticPreviewResult(
        output_path=str(output),
        audit_path=str(audit_path),
        model_path=str(transformer.model_path),
        release_allowed=False,
        note=(
            "Local semantic preview only. Mechanical evidence can qualify an "
            "artifact for manual review, but no network-egress permission is granted."
        ),
    )
