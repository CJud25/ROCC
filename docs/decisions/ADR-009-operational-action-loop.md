# ADR-009: Make an auditable operational action loop the next product slice

## Status

Proposed

## Date

2026-07-18

## Context

The synthetic demo identifies at-risk sites, ranks referral-source
organizations, and generates human-reviewed outreach drafts. The current queue
is recomputed from in-memory DataFrames and displayed read-only. It does not
persist an action ID, owner, due date, transition, outreach attempt, outcome,
follow-up, escalation, or audit history.

Geographic coverage also does not by itself prove that an organization supports
the needed job family. A persuasive draft can therefore get ahead of the
capability basis. More charts would not close this operating loop.

## Proposed decision

Make the next synthetic vertical slice:

`site risk -> capability-valid resource match -> assigned action -> outreach attempt -> outcome -> follow-up -> leadership exception`

The minimum action record includes a stable action ID, originating aggregate
risk signal, site, resource organization, job-family capability basis, owner
team, due date/SLA, status, disposition, follow-up date, Do Not Contact
enforcement, and append-only events.

The loop must remain aggregate-safe. It may refer to sites, organizations,
contracts, cohorts, and outreach actions, but it must not contain or link to
applicant rows. Synthetic partner-organization contacts may support reviewed
outreach, but contacts are never scored.

## Acceptance criteria

1. An at-risk site can create an assigned action with a reason and due date.
2. Recommendations require current geographic and job-family capability basis.
3. Do Not Contact overrides ranking and draft generation.
4. Transitions are explicit and negatively tested.
5. Attempts, outcomes, and follow-ups survive restart.
6. Executive views show overdue, blocked, and completed work using aggregates.
7. Reports include action ID, owner, as-of date, versions, and decision boundary.
8. No action, query, or export reveals an applicant identity or record.

## Alternatives considered

- **More visualization:** rejected because presentation does not create
  accountability.
- **Applicant workflow expansion:** rejected because ROCC coordinates sources,
  sites, and aggregate readiness rather than managing people.
- **Automatic email or CRM write-back:** rejected until workflow approval and
  communication controls exist.
- **Score partner contacts:** rejected because prioritization belongs at the
  organization and operating-condition level.

## Consequences

- ROCC could measure movement from aggregate insight to accountable action.
- Ownership, transitions, capability basis, and audit history would become
  explicit.
- Persistence, identity, authorization, retention, and recovery would have to
  be designed before this proposal could handle any approved operational data.
- The applicant aggregate-only boundary remains unchanged.
