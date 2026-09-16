# Third-party notices

Long Gate is an orchestration project. Third-party libraries retain their own licenses and copyrights.

## Core runtime dependencies

- pandas — BSD-3-Clause
- NumPy — BSD-3-Clause
- openpyxl — MIT
- Faker — MIT

## Optional integrations

- SynthCity (`vanderschaarlab/synthcity`) — Apache License 2.0 at the time this notice was updated.
- MOSTLY AI (`mostly-ai/mostlyai`) — Apache License 2.0 at the time this notice was updated.
- Microsoft Presidio — upstream license applies; used only as an optional local detector.
- statsmodels — BSD-3-Clause; optional local statistical executor.
- FastMCP — upstream license applies; optional MCP boundary.

## Security/development tooling

GitHub Actions may invoke CodeQL, Bandit, pip-audit, Trivy, Anchore SBOM tooling, and Dependabot. Those tools are not vendored into Long Gate.

Long Gate does not copy or relicense third-party source. Integrations are adapters/dependencies. Re-check upstream licenses and dependency metadata before releases or commercial distribution.
