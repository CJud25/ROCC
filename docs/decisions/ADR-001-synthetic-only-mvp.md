# ADR-001: Synthetic-only MVP

## Status

Accepted

## Date

2026-07-17

## Context

ROCC must demonstrate recruiting-operations workflows before any real-data
purpose, sponsorship, or governance approval exists. Real or de-identified
applicant, employee, partner, HR, timekeeping, or compliance data is not needed
to test the product's workflow and would create unsupported risk and claims.

## Decision

The public demo generates every record from a deterministic seed. All demo
sites, organizations, contacts, applicants, activities, labor hours, and
opportunities are fictional. Tables carry `synthetic_flag`; identifiers use
reserved `SYN-` prefixes; partner contacts use visible synthetic labels,
reserved phone numbers, and `example.invalid` addresses.

No real-data connector, upload, persistence route, or runtime fetch ships. The
application continues to display a synthetic banner on every page. Employer
sponsorship is required before a separately governed real-data design may even
be proposed.

Person-like synthetic applicant rows may be generated only as inputs to
aggregate calculations. The separate named-contact exception for synthetic
partner-organization outreach is recorded in ADR-024.

## Alternatives considered

- **De-identified internal data:** rejected because authorization and
  re-identification risks remain, while the workflow can be tested without it.
- **Real public organizations mixed with fictional outcomes:** rejected because
  synthetic outcomes could imply unsupported relationships or performance.
- **Realistic but unmarked identities:** rejected because the demonstration
  boundary must be visible and mechanically testable.

## Consequences

- The demo can test workflow clarity, formulas, and aggregate presentation.
- It cannot establish predictive accuracy, actual partner availability,
  official compliance status, or operational impact.
- Validation must fail when synthetic markers or reserved identity contracts
  are violated.
- Any future real-data work requires a new approved boundary and decision
  record; it cannot be enabled through configuration in this release.
