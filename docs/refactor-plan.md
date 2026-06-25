# Refactor Plan: `fred-lx` Yield Curve Module

## 0. Status (as of 2026-06-23)

Sections 1-8 below are the original design; most of it has since shipped.
Quick read on where things actually stand:

- **Done:** `ingestion/treasury_xml.py`, `curves/{par_curve,bootstrap,forwards}.py`,
  `storage/{postgres_store,duckdb_store,schema.sql}`, `viz/{curves,forwards,pca}.py`,
  `analysis/pca.py` — all built, tested, and wired into thinned notebooks.
  `curves.bootstrap` uses QuantLib's `PiecewiseLogCubicDiscount` as planned in
  Section 6. `analysis.pca.fit_yield_pca` fits on day-over-day yield changes
  (Litterman-Scheinkman convention) and now also returns a per-maturity
  variance decomposition (their Table 2), not just `explained_variance_ratio`.
- **Deliberately not built:** `ingestion/fred_api.py`. The project moved off
  FRED to Treasury XML as the sole ingestion path, so there's no second feed
  to maintain — `YieldCurve.ipynb` (FRED-based) stays only as a kept-for-history
  proof of concept, not something to migrate.
- **Deferred, not abandoned:** `analysis/risk.py` (VaR / scenario shocks from
  Section 8). Scoped out of the initial PCA work; revisit if/when risk
  simulation becomes the active project.
- **Next planned move:** once PCA work here is "finished," split this repo
  into a stripped-down data-core project (ingestion/curves/storage) plus a
  separate PCA showcase project for a portfolio piece. Whether `analysis/pca.py`
  ends up in the core repo or the showcase repo is still undecided.

## 1. Current State

`YieldCurve/DailyTreasuryParYieldCurve.ipynb` is a single 10-cell notebook that fetches
the Treasury Par Yield XML feed, parses it, bootstraps zero-coupon yields, derives
forward rates, and plots the result. `YieldCurve/YieldCurve.ipynb` does the same job
against the FRED API for "on-the-run" yields. Both are self-contained, copy-pasted
class-in-a-notebook designs:

- `DailyTreasuryParYieldAnalyzer` — fetch XML, parse XML, extract latest curve,
  bootstrap zero-coupon yields (`fsolve` per maturity), compute forward rates.
- `TreasuryYieldCurve` (other notebook) — same shape, talks to FRED instead of
  Treasury XML.
- Free-standing plotting functions (`plot_yield_curves`, `plot_forward_rates`,
  `create_summary_table`) that depend on specific DataFrame column names.
- Procedural cells that fetch, fall back to mock data inline, print, and plot.

`src/fred_lx/` exists (per `pyproject.toml`) but is an empty stub — `__init__.py`
and `py.typed` only. None of the notebook logic lives in the package.

## 2. Pain Points

1. **Logic isn't reusable.** Bootstrapping and forward-rate math are pure functions
   trapped inside a notebook class — can't be imported into a PCA or risk-simulation
   project without copy-pasting the notebook.
2. **No persistence.** Every run re-downloads the full year of XML from Treasury.
   There's no historical store, which blocks any time-series work (PCA on rate
   moves, VaR, scenario analysis) — you only ever have "today's curve" in memory.
3. **Duplicate fetches.** Cells 4 and 5 both call `fetch_treasury_xml_data` /
   `parse_xml_data` for the same year.
4. **Inline mock-data fallback duplicated** across cells instead of being a single
   testable function.
5. **Hand-rolled bootstrap.** Per-maturity `fsolve` over a manually compounded
   semi-annual coupon schedule, when `quantlib` — already a project dependency —
   has a battle-tested `PiecewiseYieldCurve`/bootstrap implementation for exactly
   this.
6. **No tests.** Forward-rate math and bootstrapping are pure, deterministic
   functions of a DataFrame — trivial to unit test — but nothing is tested.
7. **Hardcoded config.** Base URL and maturity mappings are baked into `__init__`.
8. **Plotting tightly coupled to magic strings** (`'par_yield'`, `'maturity_label'`,
   etc.), making the functions fragile and non-reusable for other curve types
   (e.g., a FRED-sourced curve has different columns).

## 3. Design Goals for the Redesign

- Pull all fetch/parse/model/storage/analysis/viz logic out of notebooks and into
  an importable `fred_lx` package — notebooks become thin orchestration/reporting
  layers.
- Introduce a durable historical store so curve data accumulates over time instead
  of being re-fetched and discarded every run.
- Make the package the shared foundation for *future* projects in this repo
  (PCA factor analysis, risk simulation), not something special-cased to the
  Treasury XML feed.
- Each layer should be unit-testable without network access (fixtures of raw
  XML/JSON in, DataFrame out).

## 4. Proposed Package Layout

```
src/fred_lx/
  config.py              # Settings: FRED_API_KEY, DB DSNs, cache dir, HTTP timeouts
  ingestion/
    __init__.py
    treasury_xml.py       # fetch_treasury_xml(year) -> str; parse_par_yields(xml) -> DataFrame
    fred_api.py            # fetch_fred_series(series_id, start, end) -> DataFrame
                            # NOT BUILT — deliberately dropped, see Section 0
  curves/
    __init__.py
    par_curve.py            # ParYieldCurve dataclass: date, maturities[], par_yields[]
    bootstrap.py            # par_to_zero(curve) -> ZeroCurve, via QuantLib bootstrap
    forwards.py              # forward_rates(zero_curve, periods) -> DataFrame
  storage/
    __init__.py
    schema.sql                # DDL for the canonical Postgres table(s)
    postgres_store.py          # upsert_par_yields(df), read_curve_history(start, end)
    duckdb_store.py            # attach_postgres(), local analytical queries/views
  analysis/
    __init__.py
    pca.py                       # fit_yield_pca(history_df, n_components) -> PCAResult
    risk.py                       # historical_var(...), pca_scenario_shock(...)
                                   # DEFERRED — not started, see Section 0
  viz/
    __init__.py
    curves.py                      # plot_yield_curves(curve, zero_curve=None)
    forwards.py                     # plot_forward_rates(forward_df, curve)
tests/
  ingestion/test_treasury_xml.py     # parse fixture XML -> expected DataFrame
  curves/test_bootstrap.py            # known par curve -> known zero curve
  curves/test_forwards.py              # known zero curve -> known forward rates
  fixtures/
    treasury_2025_sample.xml
YieldCurve/
  DailyTreasuryParYieldCurve.ipynb       # thin: ingest -> store -> bootstrap -> plot
  YieldCurve.ipynb                        # thin: FRED ingest -> plot
```

## 5. Data Flow & Storage Design

You have both Postgres and DuckDB available locally — use them for different jobs
rather than duplicating storage:

- **Postgres = system of record.** One table, append-only with an upsert on
  `(date, maturity_code)`, holding every par yield ever ingested. This is the
  durable, ACID-safe store that survives `rm -rf` of any local cache and is the
  right place for data multiple future projects (PCA, risk sim) will all read from.

  ```sql
  -- storage/schema.sql
  CREATE TABLE treasury_par_yields (
      curve_date      DATE NOT NULL,
      maturity_code   TEXT NOT NULL,   -- 'BC_10YEAR'
      maturity_years  NUMERIC NOT NULL,
      par_yield       NUMERIC,
      source          TEXT NOT NULL,   -- 'treasury_xml' | 'fred'
      ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
      PRIMARY KEY (curve_date, maturity_code, source)
  );
  ```

- **DuckDB = local analytical engine.** Rather than dual-writing, attach DuckDB
  directly to Postgres via its `postgres` extension (`ATTACH '...' AS pg
  (TYPE postgres)`) and run analytical SQL (pivots, rolling stats, window
  functions for PCA input matrices) against it with zero data duplication.
  If query latency over the network/socket becomes a problem, add a
  `CREATE TABLE AS SELECT ... FROM pg.treasury_par_yields` materialization step —
  but don't build that until it's actually slow.

- **Ingestion is idempotent.** `postgres_store.upsert_par_yields(df)` always does
  `INSERT ... ON CONFLICT (curve_date, maturity_code, source) DO UPDATE`, so
  re-running a notebook for the same year is a no-op apart from new dates.

## 6. Module Responsibilities

| Module | Responsibility | Pure/testable without network? |
|---|---|---|
| `ingestion.treasury_xml` | HTTP fetch + XML→DataFrame parsing | parse step: yes (fixture-driven) |
| `ingestion.fred_api` | HTTP fetch + JSON→DataFrame parsing — **not built**, dropped (Section 0) | parse step: yes |
| `curves.par_curve` | Typed representation of one day's curve | yes |
| `curves.bootstrap` | Par yields → zero-coupon yields (QuantLib) | yes |
| `curves.forwards` | Zero-coupon yields → forward rates | yes |
| `storage.postgres_store` | Upsert + historical read from Postgres | needs a DB, but mockable |
| `storage.duckdb_store` | Attach to Postgres, run analytical SQL | needs a DB |
| `analysis.pca` | PCA decomposition of yield curve history (level/slope/curvature factors) | yes, given a DataFrame |
| `analysis.risk` | Scenario shocks / VaR using PCA factors or historical moves — **deferred** (Section 0) | yes, given a DataFrame |
| `viz.curves` / `viz.forwards` | Plotting, takes well-typed inputs (no magic strings beyond the domain types) | n/a (visual) |

`curves.bootstrap` is the one piece worth re-implementing rather than lifting
verbatim: swap the manual `fsolve` + semi-annual coupon loop for QuantLib's
`ql.PiecewiseLogCubicDiscount` (or similar) bootstrap, since `quantlib` is already
a pinned dependency and is dramatically more robust for this exact problem
(day-count conventions, compounding, multiple curve interpolants) than hand-rolled
root-finding.

## 7. Notebook's New Role

After the refactor, `DailyTreasuryParYieldCurve.ipynb` shrinks to roughly:

```python
from fred_lx.ingestion.treasury_xml import fetch_treasury_xml, parse_par_yields
from fred_lx.storage.postgres_store import upsert_par_yields, read_curve_history
from fred_lx.curves.bootstrap import par_to_zero
from fred_lx.curves.forwards import forward_rates
from fred_lx.viz.curves import plot_yield_curves
from fred_lx.viz.forwards import plot_forward_rates

xml = fetch_treasury_xml(year=2026)
df = parse_par_yields(xml)
upsert_par_yields(df, source="treasury_xml")

latest = read_curve_history(start=df.date.max(), end=df.date.max())
zero_curve = par_to_zero(latest)
fwd = forward_rates(zero_curve)

plot_yield_curves(latest, zero_curve)
plot_forward_rates(fwd, zero_curve)
```

No more inline mock-data branches, no duplicate fetches, no class definitions
living in a notebook cell. The notebook is a report; the logic is a library.

## 8. Extensibility: PCA & Risk Simulation Projects

Because history now lives in Postgres (queryable from DuckDB), a future
`PCA/YieldCurvePCA.ipynb` or `Risk/HistoricalVaR.ipynb` notebook just becomes:

```python
from fred_lx.storage.duckdb_store import attach_postgres
from fred_lx.analysis.pca import fit_yield_pca
from fred_lx.analysis.risk import historical_var  # not built yet, see Section 0

con = attach_postgres()
history = con.sql("""
    SELECT curve_date, maturity_years, par_yield
    FROM pg.treasury_par_yields
    WHERE source = 'treasury_xml'
""").df()

pca_result = fit_yield_pca(history, n_components=3)   # level/slope/curvature
var_99 = historical_var(history, confidence=0.99, horizon_days=10)
```

`PCA/YieldCurvePCA.ipynb` now exists and matches this shape (with `fit_yield_pca`
also returning a Litterman-Scheinkman Table 2-style per-maturity variance
decomposition). `Risk/HistoricalVaR.ipynb` and `analysis/risk.py` remain
unbuilt — deferred per Section 0.

No re-implementation of fetch/parse/store plumbing — both new projects sit on top
of the same `fred_lx` package and the same Postgres table.

## 9. Migration Plan (Phased)

1. **Done.** Extracted pure functions: `parse_xml_data`,
   `calculate_zero_coupon_yields`, `calculate_forward_rates` logic moved into
   `curves/bootstrap.py` and `curves/forwards.py`, with unit tests against a
   captured XML fixture.
2. **Done.** Added `ingestion/treasury_xml.py` wrapping the HTTP fetch,
   separated from parsing.
3. **Done.** Stood up Postgres schema (`storage/schema.sql`) and
   `postgres_store.py` with upsert + read functions. Backfilled continuous
   Treasury par-yield history from 2025-01-02 onward.
4. **Done.** Bootstrap swapped to QuantLib's `PiecewiseLogCubicDiscount`.
5. **Done.** Added `duckdb_store.py` attach helper.
6. **Done.** Both notebooks rewritten to import from `fred_lx` and use the
   thin form in Section 7 (`YieldCurve.ipynb` intentionally kept as a
   FRED-based proof-of-concept, not migrated further — see Section 0).
7. **Partially done.** `analysis/pca.py` is built, tested, and backing
   `PCA/YieldCurvePCA.ipynb`. `analysis/risk.py` and a `Risk/` notebook are
   deferred, not started.

## 10. Testing Strategy

- `tests/fixtures/` holds a small captured XML response (a handful of dates) and
  a small FRED JSON response — no network calls in CI.
- `tests/curves/test_bootstrap.py` — feed a known par curve, assert zero-coupon
  output matches a hand-computed or QuantLib-verified reference within tolerance.
- `tests/curves/test_forwards.py` — feed a known zero curve, assert forward rates
  match the closed-form calculation.
- `tests/ingestion/test_treasury_xml.py` — parse the fixture XML, assert shape,
  dtypes, and date range.
- Storage and analysis modules get integration tests behind a marker
  (`@pytest.mark.postgres`) that skip if no local Postgres is reachable, so the
  fast unit suite stays network/DB-free.
