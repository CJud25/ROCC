# ADR-003: Status-only eligibility boundary

## Status

Accepted

## Date

2026-07-17

## Context

ROCC needs aggregate readiness signals, but it must not become an informal medical or disability-document repository.

## Decision

The demo contains abstract eligibility-review, documentation, and mock QDL-count statuses only. They remain inactive before the synthetic start-stage gate. No medical/disability content, document, file path, or accommodation information exists in the schema.

## Alternatives considered

- **Store synthetic diagnosis/document examples:** rejected because it normalizes a harmful future data model and adds no product value.
- **Remove all status fields:** rejected because the concept must demonstrate source-to-readiness attribution and compliance-aware workflow boundaries.

## Consequences

A future approved system must source minimal statuses from an authoritative process. ROCC will not independently determine eligibility.
