# ROCC — Recruiting & Outreach Control Center

**A synthetic, aggregates-by-design workforce and outreach demonstration for an
AbilityOne nonprofit operating context.** Part of the TENS HQ product family,
alongside [GovCon Recompete Radar](https://github.com/CJud25/GovConRadar) and
[ReconRadar](https://github.com/CJud25/ReconRadar).

> **SYNTHETIC DEMO DATA — NOT FOR EMPLOYMENT OR COMPLIANCE DECISIONS.**
> Every record is generated and fictional. No real applicant, employee, partner,
> medical, disability, or eligibility data exists anywhere in this repository.

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

## Roadmap (future — none of this is built)

- Contract-level recruiting attention driven by retention trends.
- Referral-source quality and cold-source tracking against real cadences.
- Mass-push planning when new contracts approach (via a future GovCon Recompete
  Radar handoff).
- Contract DLR trends and ODLH 75%-floor monitoring.

## Quickstart

```powershell
.\run_demo.ps1          # provisions a venv and launches the app
```

or `pip install -r requirements.txt` then `streamlit run app.py` (Python 3.11+).
Everything runs offline — the dataset is generated in memory, deterministically
seeded. To materialize it as files for inspection:
`py scripts/generate_demo_data.py` (byte-stable across runs; the output directory
is gitignored on purpose — a repo whose UI refuses per-person display does not
ship browsable person-level files, even synthetic ones).

- `docs/PRODUCT_BLUEPRINT.md` — the concept and its governance model.
- `docs/PRIVACY_AND_GOVERNANCE.md` — the boundaries, in full.
- `docs/decisions/` — the ADR lineage, including ADR-024.

## License

MIT — see [LICENSE](LICENSE).
