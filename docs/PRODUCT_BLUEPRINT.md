# ROCC Product Blueprint

ROCC - Recruiting & Outreach Control Center (part of TENS HQ) is a public,
synthetic decision-support demonstration for recruiting operations. It connects
site demand, referral-source performance, outreach planning, aggregate pipeline
health, and labor-hour scenarios without exposing or scoring applicants.

**Release boundary:** public demo 1.0  
**Data classification:** synthetic only  
**Operating model:** one aggregate-safe surface for every viewer

## 1. Product promise

ROCC helps a manager answer four operating questions:

1. Which sites may need recruiting attention?
2. Which referral sources are productive, reliable, or becoming cold?
3. Which synthetic partner organizations should receive reviewed outreach?
4. How could aggregate recruiting activity affect labor-hour planning scenarios?

ROCC is not an applicant tracking system, an employment-decision system, an
official compliance system, or an external communications platform.

Business-development workflows are maintained separately in ReconRadar.

## 2. Non-negotiable governance model

### 2.1 Synthetic until sponsorship

ROCC is **SYNTHETIC ONLY until employer sponsorship**. The public release ships
no real-data connector, upload, persistence, migration, or hidden integration
path. Every page keeps a visible synthetic-data banner.

Employer sponsorship is a prerequisite to considering a real-data phase, not
permission to ingest data. Any such phase would require a new approved purpose,
data inventory, architecture, security/privacy review, and decision record
before implementation.

### 2.2 Aggregates by design

Referral sources, sites, and contracts may be measured. Applicants may not be
listed, rendered, ranked, or scored for any viewer or role. Person-like
synthetic applicant records exist only inside the data engine as inputs to
aggregate calculations.

The rule is absolute on the applicant side:

- no applicant rows or profiles;
- no applicant names, labels, or identifiers;
- no person-level scores, recommendations, or comparisons;
- no exports or drill-through paths that reveal person records; and
- no role-based exception to any of the above.

### 2.3 Synthetic partner-contact exception

Synthetic business-to-business contacts at synthetic partner organizations may
render by name in the outreach workflow. The Resource Network contact table,
Outreach contact picker, and human-reviewed drafts may use those synthetic
business names. These contacts are not applicants, are never scored, and use
reserved synthetic contact details.

The required Pipeline Health notice is:

> applicants are never listed or scored here — aggregate pipeline health only;
> synthetic partner-org contacts appear only in the outreach workflow and are
> never scored.

### 2.4 Decision-support limits

ROCC may score or summarize systems and operating conditions: referral sources,
sites, aggregate cohorts, outreach queues, and scenarios. Outputs remain
planning aids. They are not employment decisions, official qualifying-status
decisions, staffing commitments, contract commitments, or official ODLH
determinations.

## 3. Users and operating decisions

The public demo does not implement a role selector or a permission matrix. All
nine pages are visible on one surface because every page is safe for that
surface. The demo supports discussion by leaders, operations managers,
recruiting teams, outreach teams, and compliance advisors without suggesting
that UI visibility is production authorization.

Typical decisions include:

- where aggregate site-readiness risk deserves attention;
- which referral-source relationship warrants outreach;
- what reviewed message should be carried into approved channels;
- which assumptions drive a forecast change; and
- which aggregate funnel stage or source mix needs investigation.

## 4. Current public-demo scope

### Included

- Deterministic, linked synthetic operational data generated from a seed.
- Validation of schema, references, synthetic markers, timing, and labor-hour
  math.
- Aggregate site and portfolio forecasts with explicit formula versions.
- Aggregate referral-source quality, conversion, retention, and priority
  metrics.
- A capability-aware outreach queue that enforces Do Not Contact.
- Synthetic partner-organization contact details for reviewed outreach only.
- Aggregate Pipeline Health: funnel counts, conversion rates, median
  time-in-stage, and source-mix shares.
- Human-reviewed Markdown reports and drafts with no Send action.
- Nine Streamlit pages over one shared metric and service layer.

### Explicitly excluded

- Real applicant, employee, partner, contract, payroll, HR, medical,
  disability, accommodation, or eligibility-document data.
- Applicant-level UI, export, drill-through, scoring, or recommendation.
- Data uploads, live connectors, network fetching, scraping, or real-data
  persistence.
- Automated email, messaging, CRM write-back, or external submission.
- Official compliance reporting, employment decisions, and bid/no-bid
  automation.
- Production identity, authorization, records retention, and multi-user
  operational write-back.

## 5. Information architecture

The page registry contains exactly these pages:

| Page | Manager question | Public output boundary |
|---|---|---|
| Home / Executive Overview | Where is attention needed now? | Portfolio and site aggregates |
| Site Readiness | Which sites and assumptions drive risk? | Site-level forecasts and source recommendations |
| Resource Network | Which synthetic organizations cover the need? | Organization, coverage, capability, outreach history, and synthetic B2B contacts |
| Outreach Command Center | Who should contact which organization, and what should they say? | Organization queue, synthetic contact picker, and reviewed drafts |
| Pipeline Health | Where is the aggregate funnel slowing? | Counts, rates, medians, and shares only |
| Source Performance | Which referral sources create durable readiness value? | Organization-level cohort metrics and scores |
| Ratio Forecast | How do assumptions change labor-hour scenarios? | Site and portfolio planning indicators |
| Reports | What reviewed artifact should a manager carry forward? | Synthetic Markdown downloads |
| Privacy & Governance | What may ROCC contain or claim? | Boundaries, validation results, and decision-support limits |

Shared page anatomy includes the synthetic banner, relevant controls, an
explanation of the decision being supported, formula or as-of context where
applicable, and boundary language near sensitive interpretations.

## 6. Operating workflows

### 6.1 Site attention

1. Review the portfolio forecast and trajectory.
2. Open a site to inspect the assumptions and aggregate drivers.
3. Review capability-matched referral sources.
4. Carry the next step into the outreach workflow.

### 6.2 Outreach

1. Rank synthetic partner organizations using source and site signals.
2. Remove any organization marked Do Not Contact.
3. Select a synthetic partner-organization contact.
4. Generate a draft for human review.
5. Move the reviewed text through an approved channel outside ROCC.

### 6.3 Pipeline diagnosis

1. Review stage counts and conversion rates.
2. Inspect median time-in-stage and source-mix shares.
3. Compare only aggregate segments.
4. Return to site, source, or outreach actions without revealing an applicant.

## 7. Application and metric architecture

```text
Seed + generator version
        |
        v
Linked synthetic DataFrames
        |
        v
Validation gate ---- failure ---> withhold decision outputs
        |
        v
Versioned metrics + pure aggregate summaries
        |
        v
Services: queues, drafts, reports
        |
        v
Nine aggregate-safe Streamlit pages
```

The implementation has four deliberate layers:

1. `synthetic.py` creates linked fictional records.
2. `validation.py` enforces the synthetic and relational contracts.
3. `metrics.py` owns forecast and referral-source formulas; small pure pipeline
   helpers may summarize engine records without exposing them.
4. `services.py` and `pages.py` turn shared results into actions and rendered
   outputs without redefining management-facing math.

The internal Python import path remains `tens_hq` to avoid rename churn. It is
an implementation detail; the product and all user-facing surfaces are ROCC.

## 8. Dataset generation and distribution

The generator script is the dataset story. Run:

```powershell
py scripts/generate_demo_data.py
```

The command materializes deterministic CSV files and a manifest under
`data/generated/` for local inspection. That directory is ignored and excluded
from the public repository. Regeneration with the same seed and generator
version is byte-stable.

The app itself requires no generated files on disk. It calls the deterministic
generator and uses the returned DataFrames in memory. Removing
`data/generated/` therefore does not change application behavior.

The in-memory model includes counties, sites, organizations, geographic
coverage, organization job-family capabilities, synthetic partner contacts,
outreach activities, applicant aggregation inputs, stage history, labor hours,
and synthetic opportunity inputs. Person-like applicant and stage-history rows
never cross the rendering boundary.

## 9. Metric contracts

### 9.1 Forecasts

`SYN-FORECAST-1.1` owns site forecasts, portfolio roll-ups, hiring-plan
simulation, and trajectory calculations. Portfolio ratios sum projected QDLH
and projected direct labor hours before division; they do not average site
percentages. Scenario outputs are planning indicators, not official results.

### 9.2 Referral-source performance

`SYN-PARTNER-1.1` evaluates synthetic organizations using mature aggregate
cohorts. Inputs include referral volume, application conversion, hire yield,
documentation completion, and 90-day retention with small-sample adjustment.
Scores apply to referral sources and operations, never applicants or partner
contacts. Do Not Contact overrides priority and drafting.

### 9.3 Pipeline Health

Pipeline Health computes only:

- stage funnel counts;
- adjacent-stage conversion rates;
- median time in each stage; and
- source-mix counts and shares.

Rendered columns and labels must not include applicant identifiers, display
names, individual statuses, or any other record-level value. Tests lock both
the nine-page registry and the absence of applicant identity fields.

## 10. Privacy, validation, and claims

Every generated table carries synthetic markers and reserved identifiers or
contact domains where applicable. Validation must fail on broken references,
forbidden identity patterns, invalid stage timing, or inconsistent labor-hour
math. A failed validation withholds management outputs.

ROCC excludes diagnoses, disability narratives, medical records, accommodation
information, eligibility-document images, and free-text applicant notes. It
does not determine whether a person qualifies for any program or role.

Site ratios, contract DLR trends, and portfolio ODLH scenarios must remain
visibly separate concepts. A local planning indicator cannot be presented as
an official organization-wide determination.

## 11. Release acceptance criteria

The public demo is acceptable only when:

1. all nine pages load from in-memory synthetic data;
2. the synthetic banner remains visible on every page;
3. Pipeline Health renders aggregates and no applicant identity fields;
4. synthetic partner contacts appear only in the outreach workflow and are
   never scored;
5. no real-data pathway or external sending action exists;
6. validation, tests, and source parsing gates pass; and
7. generated local data can be reproduced byte-for-byte and remains excluded
   from version control.

## 12. ROADMAP - future, not built

The following items describe owner direction only. None is implemented or
promised by the public demo:

- **Contract-level recruiting attention from retention trends:** surface where
  aggregate retention movement suggests that a contract needs earlier
  recruiting attention.
- **Referral-source quality and coldness tracking:** show quality trends,
  relationship recency, declining response, and reactivation candidates at the
  organization level.
- **Mass-push planning for approaching contracts:** prepare an aggregate,
  human-approved outreach plan when a new contract approaches, with a future
  GovConRadar handoff supplying contract timing and scope signals.
- **Contract DLR trends:** monitor planning trends by contract without turning
  them into official determinations.
- **ODLH 75%-floor monitoring:** provide organization-wide early-warning
  scenarios around the 75% floor, while preserving authoritative calculation,
  review, and certification outside ROCC.

Any roadmap item remains synthetic unless and until employer sponsorship and a
separate approved real-data design satisfy the governance gate in this
blueprint.
