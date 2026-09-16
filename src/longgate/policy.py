from __future__ import annotations

from dataclasses import dataclass
from .types import AuditResult, ReleaseClass


@dataclass
class PolicyDecision:
    allow: bool
    release_class: ReleaseClass
    reason: str

    def to_dict(self) -> dict[str, object]:
        return {"allow": self.allow, "release_class": self.release_class.value, "reason": self.reason}


class PolicyEngine:
    """Deny-by-default release policy."""

    def decide(self, release_class: ReleaseClass, audit: AuditResult | None = None) -> PolicyDecision:
        if release_class in {ReleaseClass.RAW, ReleaseClass.PSEUDONYMIZED}:
            return PolicyDecision(False, release_class, "Row-level source data is local-only by policy.")
        if release_class == ReleaseClass.AGGREGATE:
            return PolicyDecision(True, release_class, "Aggregate-only payload is eligible for release after egress scan.")
        if release_class == ReleaseClass.SYNTHETIC:
            if audit is None:
                return PolicyDecision(False, release_class, "Synthetic data requires a completed privacy audit.")
            if not audit.passed:
                return PolicyDecision(False, release_class, "Synthetic data failed the privacy gate.")
            return PolicyDecision(True, release_class, "Synthetic data passed the v0.1 privacy gate.")
        return PolicyDecision(False, release_class, "No matching allow rule; default deny.")
