# ROCC architecture

ROCC (part of TENS HQ) is a single-process Streamlit demonstration built around
deterministic in-memory synthetic data. The architecture makes the public
release inspectable and reproducible while enforcing an aggregate-only
applicant presentation boundary.

## System boundary

ROCC contains:

- a seeded synthetic domain generator;
- validation for synthetic markers, schemas, references, timing, and
  labor-hour math;
- a shared metric layer for forecasts and referral-source scoring;
- pure aggregate summaries for Pipeline Health;
- services for outreach queues, reviewed drafts, and Markdown reports; and
- nine Streamlit pages on one public surface.

ROCC contains no data upload, live connector, runtime network fetch, local
database, real-data adapter, messaging connector, or external write-back.

## Components

| Component | Responsibility | Boundary |
|---|---|---|
| `src/tens_hq/synthetic.py` | Generate linked fictional DataFrames from a seed | Person-like applicant rows remain engine inputs only |
| `src/tens_hq/validation.py` | Validate privacy, schema, reference, timing, and math contracts | Failed validation withholds decision outputs |
| `src/tens_hq/metrics.py` | Own `SYN-FORECAST-1.1` and `SYN-PARTNER-1.1` calculations | Scores sources, sites, and scenarios, never people or contacts |
| `src/tens_hq/services.py` | Build source queues, drafts, and reports | Do Not Contact overrides outreach; drafts require human review |
| `src/tens_hq/pages.py` | Render the nine-page Streamlit surface | Applicant output is aggregate-only |
| `src/tens_hq/roles.py` | Declare the ordered public page list | No role selector or page gating |
| `app.py` | Configure ROCC, controls, banner, and navigation | Uses only the public page registry |

The `tens_hq` import path is retained as a stable internal package name. It is
not user-facing branding.

## Runtime data flow

```text
seed and generator version
          |
          v
generate_demo_data()
          |
          v
linked in-memory DataFrames
          |
          +----> validate_demo_data() ---- failure ----> stop output
          |
          v
versioned metrics and aggregate summaries
          |
          v
queues, reviewed drafts, and reports
          |
          v
nine Streamlit pages
```

The app calls the generator directly and requires no dataset on disk. For local
inspection, `py scripts/generate_demo_data.py` writes deterministic artifacts to
`data/generated/`; that ignored directory is excluded from the public
repository and is never a runtime prerequisite.

## Rendering boundary

The rendering boundary is asymmetric by design:

- **Applicant side:** absolute aggregation. No applicant row, identifier, name,
  profile, status, score, export, or drill-through may render for any viewer.
- **Partner-organization side:** synthetic business contacts may render by name
  in the Resource Network and Outreach Command Center as part of the outreach
  workflow. They are never applicants and are never scored.

Pipeline Health is the only applicant-pipeline view. It presents stage counts,
conversion rates, median time-in-stage, and source-mix shares derived from
synthetic engine records.

## Page architecture

The ordered registry is:

1. Home / Executive Overview
2. Site Readiness
3. Resource Network
4. Outreach Command Center
5. Pipeline Health
6. Source Performance
7. Ratio Forecast
8. Reports
9. Privacy & Governance

All pages are visible on one public surface. This makes page-level role logic
unnecessary; a future production authorization design would be a separate
decision made only for an approved data scope.

## Metric ownership

Management-facing forecast and referral-source formulas live outside the UI.
Pages consume shared outputs and do not maintain competing implementations.
Material formula changes require a version change and updated test vectors.

Portfolio calculations aggregate QDLH and direct labor hours before calculating
a ratio. Referral-source scores use mature aggregate cohorts and small-sample
adjustment. Pipeline calculations may group person-like synthetic inputs, but
their output contract contains aggregate dimensions and measures only.

## Trust controls

- Synthetic markers and reserved identifiers/domains are validated.
- The test harness blocks socket access.
- Do Not Contact removes an organization from outreach priority.
- Drafts and reports are local, synthetic, and human-reviewed.
- No page can obtain applicant-level output through a role or navigation path.
- Generated artifacts are reproducible but excluded from version control.

## Production transition

The public demo is not a production-data foundation. Employer sponsorship would
only open a governance review; it would not activate an existing ingestion
path. A real-data proposal would require a new purpose, minimum-necessary data
contract, system-of-record boundaries, identity and authorization, retention,
security/privacy review, audit design, and new decision records before any
implementation begins.
