# ADR-024: ROCC is synthetic and aggregates by design

## Status

Accepted

## Date

2026-07-22

## Approval

Owner-approved on 2026-07-22 under the federation specification for
ROCC (part of TENS HQ).

## Context

Separating ROCC into a fresh public demo requires a governance boundary that is
true in the first release, not a future production promise. The earlier concept
allowed some roles to see synthetic applicant rows. That model conflicts with
the owner's requirement that applicant-side output be aggregate-only for
everyone.

The product also needs a narrow, practical distinction between applicants and
synthetic business contacts used to demonstrate partner outreach.

## Decision

1. **Synthetic until sponsorship.** The public demo ships no real-data pathway.
   Employer sponsorship is required before a separate real-data design may be
   considered, and sponsorship does not itself authorize ingestion.
2. **Applicant aggregates only.** Person-like synthetic applicant records may
   exist only inside the data engine as aggregation inputs. No applicant row,
   identifier, name, status, profile, score, export, or drill-through may render
   for any role.
3. **Synthetic B2B contact exception.** Synthetic partner-organization contacts
   may render by name in the Resource Network contact table, Outreach contact
   picker, and human-reviewed drafts. They are not applicants and are never
   scored.
4. **Pipeline Health replaces the applicant table.** Its output is limited to
   stage funnel counts, conversion rates, median time-in-stage, and source-mix
   shares. It carries an explicit applicant aggregate-only caption.
5. **Generated data is local, not published.**
   `py scripts/generate_demo_data.py` may materialize deterministic artifacts
   under `data/generated/` for local inspection. The directory is ignored and
   excluded from the public repository; the app generates its data in memory
   and requires nothing there at runtime.
6. **The internal package name stays stable.** The Python package and import path
   remain `tens_hq`. Renaming them would add churn without changing the
   user-facing ROCC product or its governance boundary.

## Alternatives considered

- **Keep role-gated applicant rows:** rejected because a UI role concept is not
  an authorization boundary and the applicant rule has no role exception.
- **Remove all named contacts:** rejected because synthetic business contacts
  are necessary to demonstrate reviewed partner outreach and are outside the
  applicant boundary.
- **Score contacts to choose a recipient:** rejected because operational scoring
  belongs to sources, sites, contracts, and aggregate conditions, not people.
- **Commit generated artifacts:** rejected because deterministic local
  generation is sufficient and a smaller public repository makes the runtime
  truth clearer.
- **Rename the Python package:** rejected because the cost is internal churn
  with no user or governance benefit.

## Consequences

- The public demo has one nine-page surface with no role selector.
- Pipeline Health is useful for funnel diagnosis without exposing applicants.
- The outreach workflow retains its synthetic Business contacts table, contact
  picker, and reviewed drafts.
- Tests must prevent applicant identity fields and the removed page name from
  entering the registry or rendered pipeline output.
- A future real-data phase requires a new sponsored and approved architecture;
  no configuration switch can convert this release into one.
