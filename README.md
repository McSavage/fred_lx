# FRED_LX

A FRED / US Treasury Par Yield Curve data study leading to PCA analysis on the
curve. I took José Scheinkman's course at the University of Chicago Graduate
School of Business in 1991, where I believe we read the paper. I later
recognized the method in a 1997 paper by Jon Frye of NationsBank-CRT, in
which he implements a version of the analysis for hedging a swaptions book
at Bank of America.

My intention is to break out the useful parts as a study on the 1991
Litterman-Scheinkman paper, *Common Factors Affecting Bond Returns*:

> Litterman, R., & Scheinkman, J. (1991). Common Factors Affecting Bond
> Returns. *The Journal of Fixed Income*, 1(1), 54–61.
> https://doi.org/10.3905/jfi.1991.692347
>
> [PDF photostat](https://math.nyu.edu/inmemoriam/avellaneda//Litterman1991.pdf)

And the related:

> Frye, J. (1997). Principals of Risk: Finding Value-at-Risk Through
> Factor-Based Interest Rate Scenarios. In *VAR: Understanding and Applying
> Value-at-Risk*. Risk Publications.
>
> [PDF](https://ani.stat.fsu.edu/~jfrade/HOMEWORKS/STA5707/STA5707-fall07/files/project/pdf_files/Principals_of_Risk-IMPO.pdf)

Tools for analyzing economic data from FRED (Federal Reserve Economic Data) and the US Treasury.

Ingestion, curve math, storage, PCA, and plotting live in the importable
`fred_lx` package (`src/fred_lx/`); notebooks are thin orchestration/reporting
layers on top of it. See [docs/refactor-plan.md](docs/refactor-plan.md) for the
package design and migration history.

## Contents

- [YieldCurve/YieldCurve.ipynb](YieldCurve/YieldCurve.ipynb) - Yield curve analysis using the FRED API
- [YieldCurve/DailyTreasuryParYieldCurve.ipynb](YieldCurve/DailyTreasuryParYieldCurve.ipynb) - Daily Treasury par yield curve from the Treasury XML feed
- [PCA/YieldCurvePCA.ipynb](PCA/YieldCurvePCA.ipynb) - Litterman-Scheinkman PCA (level/slope/curvature) on yield curve history

## Getting started

```bash
uv sync
```

Create a `.env` with:

```sh
FRED_API_KEY=your_key_here

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=fred_lx
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_db_password
```

Get a free FRED API key at <https://research.stlouisfed.org/useraccount/apikey>.

Ingested curve history is stored in Postgres (the `fred_lx` database, created
with `CREATE DATABASE fred_lx OWNER your_db_user;`). Apply the schema once with:

```bash
uv run python -c "from fred_lx.storage.postgres_store import connect, apply_schema; apply_schema(connect())"
```

Launch Jupyter with `uv run jupyter lab`.

### DuckDB setup

`fred_lx.storage.duckdb_store.attach_postgres()` attaches the Postgres store
to DuckDB for analytics (PCA, risk simulation, ad hoc SQL) via DuckDB's
`postgres` extension. On first use it runs `INSTALL postgres`, which
downloads the extension from `extensions.duckdb.org`.

On at least one network we've seen, that host's IPv6 route is broken and the
download hangs for ~2 minutes instead of failing fast and falling back to
IPv4. If `INSTALL postgres` (or anything calling `attach_postgres()`) hangs,
install it manually over IPv4 instead:

```bash
curl -4 -fsS -o /tmp/postgres_scanner.duckdb_extension.gz \
  http://extensions.duckdb.org/v1.5.4/linux_amd64/postgres_scanner.duckdb_extension.gz
gunzip -kf /tmp/postgres_scanner.duckdb_extension.gz
mkdir -p ~/.duckdb/extensions/v1.5.4/linux_amd64
mv /tmp/postgres_scanner.duckdb_extension ~/.duckdb/extensions/v1.5.4/linux_amd64/
```

After that, `INSTALL postgres; LOAD postgres` finds the extension locally
and never touches the network. Adjust the version/platform in the paths
above to match your `duckdb` package version if it differs from `v1.5.4`.

## Tests

```bash
uv run pytest
```

Tests marked `postgres` require a reachable Postgres database and are
automatically skipped if one isn't configured.
