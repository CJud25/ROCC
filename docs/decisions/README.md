# Architecture decision records

This directory records the decision lineage for the ROCC synthetic operations
demo. The separate packet product's decision records live with ReconRadar. The
numbering gaps are intentional; they preserve lineage without importing
decisions from the other product.

| ADR | Status | Decision |
|---|---|---|
| [ADR-001](ADR-001-synthetic-only-mvp.md) | Accepted | Use deterministic synthetic data only |
| [ADR-002](ADR-002-one-versioned-metric-layer.md) | Accepted | Keep management formulas in one versioned metric layer |
| [ADR-003](ADR-003-status-only-eligibility-boundary.md) | Accepted | Keep eligibility concepts status-only and outside document storage |
| [ADR-004](ADR-004-site-indicator-vs-official-odlh.md) | Accepted | Separate planning indicators from official ODLH determinations |
| [ADR-005](ADR-005-human-reviewed-drafts-only.md) | Accepted | Produce drafts without automatic sending |
| [ADR-009](ADR-009-operational-action-loop.md) | Proposed | Make an auditable aggregate-safe action loop the next product slice |
| [ADR-010](ADR-010-forecast-1-1-planning-simulation.md) | Accepted | Keep SYN-FORECAST-1.1 in the shared metric layer |
| [ADR-024](ADR-024-rocc-aggregates-by-design.md) | Accepted | Make synthetic-only and applicant aggregates-by-design binding |

Accepted records describe current constraints or implementation decisions.
Proposed records describe future work and do not imply that the capability is
built.
