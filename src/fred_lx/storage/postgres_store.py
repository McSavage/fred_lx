"""Postgres persistence for Treasury par yield history.

This is the canonical, durable store: ingestion writes here, and everything
else (DuckDB analytics, PCA, risk simulation) reads from it. See
docs/refactor-plan.md section 5.
"""

import datetime as dt
from pathlib import Path

import pandas as pd
import psycopg

from fred_lx.config import settings
from fred_lx.curves.par_curve import MATURITY_MAPPING

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def connect(dsn: str | None = None) -> psycopg.Connection:
    """Open a new connection (caller is responsible for closing it)."""
    return psycopg.connect(dsn or settings.postgres_dsn)


def apply_schema(conn: psycopg.Connection) -> None:
    """Create the treasury_par_yields table if it doesn't already exist."""
    conn.execute(SCHEMA_PATH.read_text())
    conn.commit()


def upsert_par_yields(
    conn: psycopg.Connection, df: pd.DataFrame, source: str
) -> int:
    """Upsert a wide par-yield DataFrame into the canonical store.

    Args:
        conn: Open connection.
        df: Wide DataFrame as returned by
            ``fred_lx.ingestion.treasury_xml.parse_par_yields`` — one row
            per date, one column per ``BC_*`` maturity code.
        source: Provenance tag, e.g. ``"treasury_xml"`` or ``"fred"``.

    Returns:
        Number of (date, maturity) rows written.
    """
    maturity_codes = [code for code in MATURITY_MAPPING if code in df.columns]
    if df.empty or not maturity_codes:
        return 0

    long_df = df.melt(
        id_vars=["date"],
        value_vars=maturity_codes,
        var_name="maturity_code",
        value_name="par_yield",
    ).dropna(subset=["par_yield"])

    if long_df.empty:
        return 0

    rows = [
        (
            row.date,
            row.maturity_code,
            MATURITY_MAPPING[row.maturity_code],
            row.par_yield,
            source,
        )
        for row in long_df.itertuples(index=False)
    ]

    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO treasury_par_yields
                (curve_date, maturity_code, maturity_years, par_yield, source)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (curve_date, maturity_code, source)
            DO UPDATE SET
                par_yield = EXCLUDED.par_yield,
                maturity_years = EXCLUDED.maturity_years,
                ingested_at = now()
            """,
            rows,
        )
    conn.commit()
    return len(rows)


def read_curve_history(
    conn: psycopg.Connection,
    start: dt.date,
    end: dt.date,
    source: str = "treasury_xml",
) -> pd.DataFrame:
    """Read long-format par yield history for one source between two dates (inclusive)."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT curve_date AS date, maturity_code, maturity_years, par_yield
            FROM treasury_par_yields
            WHERE source = %s AND curve_date BETWEEN %s AND %s
            ORDER BY curve_date, maturity_years
            """,
            (source, start, end),
        )
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]

    return pd.DataFrame(rows, columns=columns)
