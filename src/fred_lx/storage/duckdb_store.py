"""DuckDB analytical layer, attached directly to the Postgres canonical store.

No separate copy of the data is kept locally: DuckDB's `postgres` extension
queries Postgres directly, so analytics (PCA, risk simulation, ad hoc SQL)
run with DuckDB's window functions / pivots and zero ETL step. See
docs/refactor-plan.md section 5.

Requires the `postgres` extension to be installed once -- see the README's
"DuckDB setup" section if `INSTALL postgres` hangs on your network.
"""

import duckdb

from fred_lx.config import settings

PG_ALIAS = "pg"


def attach_postgres(
    con: duckdb.DuckDBPyConnection | None = None,
) -> duckdb.DuckDBPyConnection:
    """Attach the Postgres canonical store to a DuckDB connection as `pg`.

    Args:
        con: Existing DuckDB connection to attach to. Defaults to a new
            in-memory connection.

    Returns:
        The connection, with e.g. ``pg.treasury_par_yields`` queryable.
    """
    if con is None:
        con = duckdb.connect()

    con.execute("INSTALL postgres")
    con.execute("LOAD postgres")

    dsn = (
        f"host={settings.postgres_host} port={settings.postgres_port} "
        f"dbname={settings.postgres_db} user={settings.postgres_user} "
        f"password={settings.postgres_password}"
    )
    con.execute(f"ATTACH '{dsn}' AS {PG_ALIAS} (TYPE postgres, READ_ONLY)")
    return con
