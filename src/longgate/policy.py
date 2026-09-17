from __future__ import annotations

from dataclasses import dataclass

from .types import AuditResult, ReleaseClass


@dataclass
class PolicyDecision:
    allow: bool
    release_class: ReleaseClass
    reason: str

    def to_dict(self) -> dict[str, object]:
        return {
            "allow": self.allow,
            "release_class": self.release_class.value,
            "reason": self.reason,
        }


class PolicyEngine:
    """Deny-by-default release policy.

    Evidence is not authorization. In the pre-1.0 baseline, row-level synthetic
    release remains hard-locked even when the privacy audit passes.
    """

    def decide(
        self,
        release_class: ReleaseClass,
        audit: AuditResult | None = None,
        *,
        aggregate_validated: bool = False,
    ) -> PolicyDecision:
        if release_class in {ReleaseClass.RAW, ReleaseClass.PSEUDONYMIZED}:
            return PolicyDecision(
                False,
                release_class,
                "Row-level source data is local-only by policy.",
            )

        if release_class == ReleaseClass.AGGREGATE:
            if not aggregate_validated:
                return PolicyDecision(
                    False,
                    release_class,
                    "Aggregate release requires a validated disclosure-limited payload.",
                )
            return PolicyDecision(
                True,
                release_class,
                "Disclosure-limited aggregate payload passed the aggregate guard and is eligible for final egress scan.",
            )

        if release_class == ReleaseClass.SYNTHETIC:
            if audit is None:
                return PolicyDecision(
                    False,
                    release_class,
                    "Synthetic data requires a completed privacy audit.",
                )
            if not audit.passed:
                return PolicyDecision(
                    False,
                    release_class,
                    "Synthetic data failed the privacy gate.",
                )
            return PolicyDecision(
                False,
                release_class,
                "Synthetic audit passed, but pre-1.0 policy hard-locks row-level synthetic release; evidence is not authorization.",
            )

        return PolicyDecision(False, release_class, "No matching allow rule; default deny.")
