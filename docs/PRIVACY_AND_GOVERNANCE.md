# ROCC privacy and governance statement

ROCC (part of TENS HQ) is a synthetic recruiting-operations demonstration. It
measures referral sources, sites, aggregate cohorts, and planning scenarios -
never the worth, disability status, eligibility, or employability of a person.

## Binding commitments

### Synthetic only until employer sponsorship

The public release uses synthetic data only and ships no real-data pathway.
Employer sponsorship is required before any real-data phase can be considered.
Sponsorship alone is not approval to ingest data: a new purpose, data inventory,
minimum-necessary design, security/privacy review, and accepted decision record
must come first.

Every application page retains a visible synthetic-data banner. Synthetic
labels, reserved IDs, `example.invalid` contact addresses, and validation rules
make the boundary testable rather than aspirational.

### Aggregates by design

The applicant side is aggregate-only for every viewer. ROCC does not render,
export, rank, compare, or score applicants. No role may reveal applicant rows,
names, labels, identifiers, individual statuses, or profiles. Person-like
synthetic records exist only within the data engine as inputs to aggregate
funnel counts, conversion rates, median time-in-stage, source-mix shares, source
performance, and planning calculations.

Pipeline Health states the rule directly:

> applicants are never listed or scored here — aggregate pipeline health only;
> synthetic partner-org contacts appear only in the outreach workflow and are
> never scored.

### Synthetic B2B contact exception

Synthetic partner-organization contacts may render by name in the outreach
workflow. This includes the Resource Network Business contacts table, the
Outreach contact picker, and human-reviewed draft text. These records represent
fictional business contacts, not applicants. They use synthetic contact details
and are never scored.

The exception does not permit applicant names, real contact data, person-level
analytics, automated selection, or automated communication.

## Prohibited data and behavior

ROCC excludes real applicant or employee information, diagnoses, disability
narratives, medical records, accommodation information, eligibility-document
images, payroll data, and free-text applicant notes. It has no upload control,
real-data connector, hidden integration route, runtime web fetch, or Send
button.

The demo must not:

- make or recommend employment decisions;
- determine qualifying or documentation status for a person;
- expose applicant-level results through navigation, export, or drill-through;
- score synthetic partner contacts;
- claim an official DLR or ODLH determination;
- make staffing, partner, contract, or external communication commitments; or
- use synthetic outcomes as proof of real-world performance.

## Data handling

The application generates its DataFrames in memory from a deterministic seed
and does not require data files on disk. The optional local command
`py scripts/generate_demo_data.py` materializes reproducible artifacts under
`data/generated/`. That directory is ignored and excluded from the public
repository.

Generated applicant and stage-history records are aggregation inputs, not
presentation records. Synthetic partner contacts are the only named-person
records allowed to cross the rendering boundary, and only in the outreach
workflow described above.

## Decision-support limits

Site ratios, contract DLR trends, and organization-wide ODLH scenarios are
planning indicators. ROCC does not issue an official compliance determination
or certification. Referral-source scores describe aggregate source operations;
they do not score applicants or contacts. Draft messages and reports require
human review and movement through approved channels outside the app.

## Governance gate for any future real-data proposal

A sponsored proposal must define and receive approval for:

1. a specific operational purpose and accountable owner;
2. authoritative system-of-record boundaries;
3. a minimum-necessary field inventory with applicant aggregation preserved;
4. identity, authorization, query, export, and negative-test controls;
5. retention, correction, deletion, legal-hold, and audit rules;
6. security, privacy, accessibility, compliance, and records reviews;
7. incident response, monitoring, backup, and recovery; and
8. a migration plan that introduces no silent real-data path into the public
   demo.

Until those decisions are separately accepted and implemented, ROCC remains
synthetic only.
