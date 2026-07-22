# ADR-002: One versioned metric layer

## Status

Accepted

## Date

2026-07-17

## Context

ROCC presents related operational measures across several pages. Re-creating
management-facing formulas inside each page would produce conflicting answers
and make changes difficult to verify.

## Decision

Forecasts, portfolio roll-ups, hiring-plan simulations, trajectories, and
referral-source scores live outside the UI in testable Python modules with
explicit formula versions. Streamlit pages consume those shared outputs and do
not redefine their math.

Small pure helpers may compute Pipeline Health aggregates from the synthetic
engine's records. Their output contract is aggregate-only and is tested against
the applicant rendering prohibition.

Scores apply to referral-source organizations and operations, never applicants
or partner contacts.

## Alternatives considered

- **Page-local Pandas calculations:** faster initially, but difficult to test
  consistently and prone to drift.
- **A reporting-tool formula layer as the first source of truth:** useful for
  presentation, but weaker for generator-driven test vectors and application
  workflow prototyping.
- **One module per page:** rejected because pages share inputs and management
  definitions.

## Consequences

- All consumers must reproduce the shared test vectors.
- Material formula changes require a new version and updated tests.
- UI refactoring cannot silently change management-facing math.
- Aggregate pipeline helpers must preserve a schema that contains no applicant
  identity fields.
