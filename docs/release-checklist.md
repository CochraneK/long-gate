# Release checklist

Long Gate is security-sensitive. A version tag should represent a reviewed state, not merely a packaging event.

## Before tagging

- [ ] unit tests green
- [ ] privacy/security invariant tests green
- [ ] CodeQL green
- [ ] Bandit green
- [ ] pip-audit reviewed
- [ ] Trivy green/reviewed
- [ ] SBOM generated
- [ ] README claims match implemented behavior
- [ ] CHANGELOG updated
- [ ] THIRD_PARTY_NOTICES reviewed
- [ ] optional dependency licenses rechecked
- [ ] benchmark fixtures are synthetic
- [ ] Trust Report contains no raw example values
- [ ] release posture for row-level egress is explicit
- [ ] version updated in package and citation metadata

## After tagging

The `release-build` workflow builds wheel/sdist artifacts.

PyPI publication is intentionally not automatic yet.
