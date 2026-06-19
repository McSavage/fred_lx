# FRED_LX

Jupyter notebooks for analyzing economic data from FRED (Federal Reserve Economic Data) and the US Treasury.

## Contents

- [YieldCurve/YieldCurve.ipynb](YieldCurve/YieldCurve.ipynb) - Yield curve analysis using the FRED API
- [YieldCurve/DailyTreasuryParYieldCurve.ipynb](YieldCurve/DailyTreasuryParYieldCurve.ipynb) - Daily Treasury par yield curve from the Treasury XML feed

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
