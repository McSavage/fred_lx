import datetime as dt

import pandas as pd
import pytest

from fred_lx.storage.duckdb_store import attach_postgres
from fred_lx.storage.postgres_store import upsert_par_yields

pytestmark = pytest.mark.postgres


def test_attach_postgres_exposes_treasury_par_yields_table(pg_conn):
    con = attach_postgres()
    tables = con.sql(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
    ).df()
    assert "treasury_par_yields" in tables["table_name"].tolist()


def test_attach_postgres_reads_data_written_via_postgres_store(pg_conn):
    date = dt.date(2025, 1, 2)
    df = pd.DataFrame([{"date": date, "BC_10YEAR": 4.57}])
    upsert_par_yields(pg_conn, df, source="test")

    con = attach_postgres()
    result = con.sql(
        "SELECT par_yield FROM pg.treasury_par_yields "
        "WHERE source = 'test' AND maturity_code = 'BC_10YEAR' AND curve_date = ?",
        params=[date],
    ).df()

    assert len(result) == 1
    assert float(result.iloc[0]["par_yield"]) == pytest.approx(4.57)


def test_attach_postgres_accepts_an_existing_connection(pg_conn):
    import duckdb

    existing = duckdb.connect()
    returned = attach_postgres(existing)
    assert returned is existing
    # Should not raise -- pg is attached on the same connection object.
    returned.sql("SELECT count(*) FROM pg.treasury_par_yields").df()
