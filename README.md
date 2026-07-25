# ROCC — Recruiting & Outreach Control Center

**Every record in this repository is synthetic by design — that is the
governance point, not a limitation.** ROCC is a workforce and outreach control
center for an AbilityOne nonprofit operating context: referral sources, sites,
and aggregate pipeline stages get measured, and applicants never do. There is
no hosted deployment — `.\run_demo.ps1` provisions a virtualenv and boots it
locally.

![ROCC Executive Command Brief: a 90-day planning indicator, gap to target,
ready hires needed and at-risk site count as four KPI cards, a live "ready hires
we can commit" slider with three simulated KPIs, and a portfolio trajectory
chart](docs/assets/rocc-home.png)

*The default page, screenshotted from a local run of this repository. Every
figure on it is computed at run time by the deterministic synthetic generator;
none of it is hand-entered. The synthetic-data banner sits in the sidebar on
every page, and the planning-indicator banner shown here also appears on Site
Readiness and Ratio Forecast — the other two surfaces that project a ratio.*

> **SYNTHETIC DEMO DATA — NOT FOR EMPLOYMENT OR COMPLIANCE DECISIONS.**
> Every record is generated and fictional. No real applicant, employee, partner,
> medical, disability, or eligibility data exists anywhere in this repository.

Part of the TENS HQ product family, alongside
[GovCon Recompete Radar](https://github.com/CJud25/GovConRadar) and
[ReconRadar](https://github.com/CJud25/ReconRadar).

## The two rules (ADR-024)

1. **Synthetic only, until sponsorship.** No real-data pathway ships. A real-data
   version happens only under employer sponsorship, in a separate trust boundary.
2. **Aggregates by design.** Referral sources, sites, and contracts get measured —
   **applicants never do.** No applicant-level rows, identifiers, or statuses
   render anywhere (test-enforced). One documented exception: synthetic
   partner-organization **business contacts** may appear by name in three synthetic
   surfaces — the Resource Network contact table, the Outreach contact picker,
   and human-reviewed draft messages — they are B2B contacts, never applicants,
   and never scored.

## What it demonstrates

Nine pages: an executive overview, site readiness, the resource/partner network,
an outreach command center (contact recency, neglected sources, human-reviewed
drafts), **Pipeline Health** (aggregate funnel counts, stage conversion, and
time-in-stage — no people listed), source performance, a labeled ratio-forecast
planning simulation, reports, and the privacy & governance statement.

![ROCC Pipeline Health: synthetic referral, application, hire and referral-source
totals, a stage funnel bar chart from Referred down to Eligibility Cleared, and a
stage conversion table](docs/assets/rocc-pipeline-health.png)

*Pipeline Health is where the second rule is easiest to check. The funnel is
built from person-like synthetic records that never leave the data engine: the
page renders counts, conversion rates, medians and shares, and
`tests/test_ui_contract.py` fails the build if an applicant identifier or
display label reaches a rendered frame.*

## Roadmap (future — none of this is built)

- Contract-level recruiting attention driven by retention trends.
- Referral-source quality and cold-source tracking against real cadences.
- Mass-push planning when new contracts approach (via a future GovCon Recompete
  Radar handoff).
- Contract direct-labor-ratio (DLR) trends and direct-labor-hours (ODLH) 75%-floor monitoring.

> Acronyms: QDLH = Qualifying Direct Labor Hours, DLH = Direct Labor Hours,
ratio = QDLH / DLH (the AbilityOne 75% requirement). A full glossary is on the
Privacy & Governance page.

## Quickstart

```powershell
.\run_demo.ps1          # provisions a venv and launches the app
```

or `pip install -r requirements.txt` then `streamlit run app.py` (Python 3.11+;
CI provisions 3.11). Everything runs offline — the dataset is generated in
memory, deterministically seeded. To materialize it as files for inspection:
`py scripts/generate_demo_data.py` (byte-stable across runs; the output directory
is gitignored on purpose — a repo whose UI refuses per-person display does not
ship browsable person-level files, even synthetic ones).

The gate, and what CI runs on every push:

```powershell
python -m pytest
python -m ruff check .
python scripts/validate_demo_data.py
```

- `docs/PRODUCT_BLUEPRINT.md` — the concept and its governance model.
- `docs/PRIVACY_AND_GOVERNANCE.md` — the boundaries, in full.
- `docs/decisions/` — the ADR lineage, including ADR-024.

## How this was built

I specified this product, cut it into gated slices, and verified each one; AI
agents wrote most of the line-level code. The co-author trailers in the commit
history make that split checkable, not asserted.

No slice landed until it came back green on the repo's own gate — today
`python -m pytest`, `python -m ruff check .`, and
`python scripts/validate_demo_data.py`, all of which CI runs — and an
independent adversarial review pass went at it first, looking for what I would
want to believe. Commit `1b7b24c` ("writer-review fix") is what that pass leaves
behind.

The catch I am proudest of is in ADR-024. An earlier design let a role selector
decide which viewers saw synthetic applicant-level rows, and it read like a
privacy control. It is not one. A dropdown in a demo UI is a display preference,
not an authorization boundary — the rows are in the process either way, so
"recruiters see people, executives do not" protects nobody. I deleted the role
gate instead of tuning it, and applicant output became aggregate-only for every
viewer.

The commit history shows AI co-authorship. The judgment calls — what to refuse
to compute, what to delete, which wording was overstated — are the part worth
evaluating.

## License

MIT — see [LICENSE](LICENSE).
