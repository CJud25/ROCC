# Changelog

This file tracks releases, not individual commits. Work merged to `main` after
the last released version is listed under Unreleased. The version strings in
`pyproject.toml` and `src/tens_hq/constants.py` still read `1.0.0` because no
newer version has been cut; `git log` is the authority on what has shipped.

## [Unreleased]

### Added

- Data-driven, site-specific manager action plan on Site Readiness.
- Overdue-queue shading and a flagged weakest funnel step on the triage view.
- Friendly column headers on leadership tables, from a shared label map.
- Glossary, plus first-use expansions of ODLH, DLR, and QDLH.
- Permissive `ruff` gate in CI and an advisory, pinned `pip-audit` scan; CI also
  builds the demo container, boots it, and probes its health endpoint.

### Changed

- Planning controls moved above the navigation fold in the sidebar.
- Ratio-forecast wording: formula id moved into a caption, the internal planning
  floor relabeled, the `Hq = Hd` planning assumption disclosed, and the
  unreachable-target guard described honestly (it does not trigger under the
  current full-QDL assumption).
- The two "ready hires" measures reconciled into distinct labels with coverage
  captions.
- Home hero KPIs re-cut for legibility: short labels, the gap stated in words.
- Streamlit usage telemetry disabled, for an offline posture.
- `run_demo.ps1` aligned to the runtime dependency list.
- Validation counts derived from constants and covered by a drift test instead
  of being hand-maintained; unused imports and locals removed.
- README rule 2 now names all three synthetic contact surfaces, matching
  ADR-024.

### Fixed

- Resource Network renders a zero-result empty state before its chart and table.
- Generated outreach draft fields are read-only.
- The log-scale x-axis on Source Performance is labeled.
- The outreach queue is described as a read-only planning view; ADR-009 is
  Proposed, not built.

### Security

- The site-name heading interpolation is HTML-escaped.
- `pip-audit` is exact-pinned in CI, matching every other pinned dependency.

## [1.0.0] - 2026-07-22

### Added

- Initial public release of ROCC - Recruiting & Outreach Control Center.
- Nine-page synthetic recruiting-operations demonstration.
- Aggregate-only Pipeline Health with no applicant listing or scoring.
- Deterministic in-memory data generation, validation, forecasts,
  referral-source metrics, outreach planning, and reviewed reports.
- Explicit synthetic-only and aggregates-by-design governance.
