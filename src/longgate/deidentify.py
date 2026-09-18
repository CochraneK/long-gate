from __future__ import annotations

import html
from dataclasses import asdict, dataclass
from pathlib import Path

from .documents import extract_document_text
from .semantic import (
    LocalLlamaCppTransformer,
    SemanticPreviewAudit,
    _safe_chunks,
    audit_semantic_preview,
)
from .unstructured import redact_text_local
from .utils import atomic_write_text, sha256_file, utc_now, write_json


@dataclass(frozen=True)
class DeidentifyAttempt:
    round: int
    failed_conditions: list[str]
    eligible_for_manual_review: bool
    direct_pii_hits: int
    reused_number_tokens: int
    character_ngram_reuse_rate: float
    distinctive_token_reuse_rate: float
    transformed_characters: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DeidentifyResult:
    status: str
    output_path: str
    audit_path: str
    report_path: str
    model_path: str
    attempts: int
    eligible_for_manual_review: bool
    manual_review_required: bool
    automatic_release_allowed: bool
    release_allowed: bool
    next_actions: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _attempt_from_audit(round_number: int, audit: SemanticPreviewAudit) -> DeidentifyAttempt:
    evidence = audit.release_evidence
    return DeidentifyAttempt(
        round=round_number,
        failed_conditions=list(evidence.failed_conditions),
        eligible_for_manual_review=evidence.eligible_for_manual_review,
        direct_pii_hits=audit.direct_pii_hits,
        reused_number_tokens=audit.reused_number_tokens,
        character_ngram_reuse_rate=audit.character_ngram_reuse_rate,
        distinctive_token_reuse_rate=audit.distinctive_token_reuse_rate,
        transformed_characters=audit.transformed_characters,
    )


def _render_report(
    *,
    output_name: str,
    input_sha256: str,
    model_file: str,
    attempts: list[DeidentifyAttempt],
    status: str,
    next_actions: list[str],
) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{attempt.round}</td>"
        f"<td>{'PASS' if attempt.eligible_for_manual_review else 'RETRY / HOLD'}</td>"
        f"<td>{attempt.direct_pii_hits}</td>"
        f"<td>{attempt.reused_number_tokens}</td>"
        f"<td>{attempt.character_ngram_reuse_rate:.2%}</td>"
        f"<td>{attempt.distinctive_token_reuse_rate:.2%}</td>"
        f"<td>{html.escape(', '.join(attempt.failed_conditions) or 'none')}</td>"
        "</tr>"
        for attempt in attempts
    )
    actions = "".join(f"<li>{html.escape(action)}</li>" for action in next_actions)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Long Gate Semantic Trust Report</title>
<style>
body{{font-family:system-ui,-apple-system,sans-serif;max-width:1050px;margin:40px auto;padding:0 20px;line-height:1.5;color:#18212f}}
.card{{border:1px solid #d8dee8;border-radius:14px;padding:18px;margin:16px 0;background:#fff}}
code{{background:#f2f4f8;padding:2px 5px;border-radius:5px;word-break:break-all}}
table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #d8dee8;padding:8px;text-align:left;vertical-align:top}}th{{background:#f4f7fb}}
.badge{{display:inline-block;padding:5px 10px;border-radius:999px;background:#eef2f7;font-weight:700}}
</style>
</head>
<body>
<h1>Long Gate · Semantic Trust Report</h1>
<p class="badge">{html.escape(status)}</p>
<div class="card">
<h2>What this report means</h2>
<p>This document reports local semantic de-identification evidence. It does <strong>not</strong> certify anonymity and never grants network egress automatically.</p>
</div>
<div class="card">
<h2>Local processing</h2>
<p>Input SHA-256: <code>{html.escape(input_sha256)}</code></p>
<p>Local model file: <code>{html.escape(model_file)}</code></p>
<p>Output file: <code>{html.escape(output_name)}</code></p>
<p>Local directory paths, source text, and transformed text are intentionally not embedded in this report.</p>
</div>
<div class="card">
<h2>Remediation rounds</h2>
<table><thead><tr><th>Round</th><th>Decision</th><th>PII hits</th><th>Reused numbers</th><th>N-gram reuse</th><th>Distinctive-token reuse</th><th>Failed conditions</th></tr></thead><tbody>{rows}</tbody></table>
</div>
<div class="card">
<h2>Next actions</h2><ul>{actions}</ul>
</div>
<p>Generated locally by Long Gate at {html.escape(utc_now())}. No remote assets are used.</p>
</body></html>"""


def deidentify_local(
    input_path: str | Path,
    model_path: str | Path,
    output_path: str | Path,
    *,
    max_rounds: int = 2,
    max_tokens: int = 512,
    chunking: str = "none",
    chunk_size: int = 3000,
) -> DeidentifyResult:
    """Run bounded local semantic remediation while keeping egress fail-closed."""
    if not 1 <= max_rounds <= 3:
        raise ValueError("max_rounds must be between 1 and 3.")

    input_file = Path(input_path).expanduser().resolve()
    output = Path(output_path).expanduser().resolve()
    if output == input_file:
        raise ValueError("Refusing to overwrite the input file.")
    input_sha256 = sha256_file(input_file)
    source, _, _, _ = extract_document_text(input_file)
    if not source.strip():
        raise ValueError("Input document contains no extractable text.")

    if chunking not in {"none", "safe"}:
        raise ValueError("chunking must be 'none' or 'safe'.")
    transformer = LocalLlamaCppTransformer(model_path)
    current = redact_text_local(source)
    attempts: list[DeidentifyAttempt] = []
    final_text = current
    final_audit: SemanticPreviewAudit | None = None
    risk_focus: list[str] | None = None

    for round_number in range(1, max_rounds + 1):
        chunks = [current] if chunking == "none" else _safe_chunks(current, chunk_size)
        final_text = "\n\n".join(
            transformer.transform(
                chunk,
                max_tokens=max_tokens,
                risk_focus=risk_focus,
            )
            for chunk in chunks
        )
        final_audit = audit_semantic_preview(source, final_text)
        attempt = _attempt_from_audit(round_number, final_audit)
        attempts.append(attempt)
        if attempt.eligible_for_manual_review:
            break
        current = final_text
        risk_focus = attempt.failed_conditions

    if final_audit is None:  # pragma: no cover - defensive
        raise RuntimeError("No semantic de-identification attempt was completed.")

    eligible = final_audit.release_evidence.eligible_for_manual_review
    status = "MANUAL_REVIEW_CANDIDATE" if eligible else "LOCAL_ONLY"
    next_actions = (
        [
            "Review the transformed text locally for rare-event, relationship, and combination-uniqueness leakage.",
            "Keep the artifact local; the current semantic baseline does not authorize network egress.",
        ]
        if eligible
        else [
            "Keep the artifact local.",
            "Review the failed_conditions in the audit and generalize or remove the remaining identifying context.",
            "Re-run longgate deidentify after local edits if another bounded attempt is justified.",
        ]
    )

    atomic_write_text(output, final_text, encoding="utf-8")
    if sha256_file(input_file) != input_sha256:
        raise RuntimeError("Input file changed during processing; refusing to report success.")

    audit_path = output.with_name(output.name + ".audit.json")
    report_path = output.with_name(output.name + ".trust-report.html")
    model_file = Path(transformer.model_path).name
    payload = {
        "format": "long-gate-semantic-deidentify-v1",
        "status": status,
        "input_sha256": input_sha256,
        "output_sha256": sha256_file(output),
        "model_file": model_file,
        "attempts": [attempt.to_dict() for attempt in attempts],
        "final_audit": final_audit.to_dict(),
        "eligible_for_manual_review": eligible,
        "manual_review_required": True,
        "automatic_release_allowed": False,
        "release_allowed": False,
        "next_actions": next_actions,
        "chunking": chunking,
        "chunk_count": (
            1 if chunking == "none" else len(_safe_chunks(source, chunk_size))
        ),
    }
    write_json(audit_path, payload)
    atomic_write_text(
        report_path,
        _render_report(
            output_name=output.name,
            input_sha256=str(payload["input_sha256"]),
            model_file=model_file,
            attempts=attempts,
            status=status,
            next_actions=next_actions,
        ),
        encoding="utf-8",
    )

    return DeidentifyResult(
        status=status,
        output_path=str(output),
        audit_path=str(audit_path),
        report_path=str(report_path),
        model_path=str(transformer.model_path),
        attempts=len(attempts),
        eligible_for_manual_review=eligible,
        manual_review_required=True,
        automatic_release_allowed=False,
        release_allowed=False,
        next_actions=next_actions,
    )
