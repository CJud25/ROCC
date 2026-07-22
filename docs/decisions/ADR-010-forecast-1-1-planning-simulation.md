# ADR-010: SYN-FORECAST-1.1 stays in the versioned metric layer

## Status

Accepted

## Date

2026-07-18

## Context

ROCC presents ready-hire commitment simulations, portfolio gap roll-ups, and a
six-horizon trajectory fan. These are synthetic planning calculations. Without
a recorded ownership decision, pages could grow local formulas that drift from
the tested contract and from one another.

## Decision

`metrics.py` owns `SYN-FORECAST-1.1` as one version-stamped planning contract:

- `forecast_sites` produces site ready-hire gaps and projected labor-hour
  planning indicators.
- `portfolio_summary` sums the site results into a portfolio view.
- `apply_hiring_plan` powers the live commitment simulation.
- `trajectory` produces the six-horizon, 30-through-180-day projection fan.

`render_home`, `render_site_readiness`, and `render_ratio_forecast` consume
these outputs and must not redefine the underlying math. Forecasts remain
research and planning aids; they are not staffing commitments, employment
decisions, or official DLR/ODLH determinations.

## Alternatives considered

- **Page-local calculation:** faster to write, but it recreates the drift that
  ADR-002 exists to prevent and weakens shared test vectors.
- **A new metric module for each forecast surface:** unnecessary surface area;
  the features share forecast inputs and definitions.
- **Person-level forecasting:** rejected because aggregate cohort assumptions
  are sufficient and individual prediction conflicts with ROCC governance.

## Consequences

- Any material change to ready-hire, trajectory, or portfolio math requires a
  new `SYN-FORECAST-1.x` version and updated test vectors.
- Pages can change presentation without changing the formula contract.
- Portfolio ratios sum projected QDLH and direct labor hours before division;
  site percentages are not averaged.
- Forecast output remains synthetic and aggregate-only.
