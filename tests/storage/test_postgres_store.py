import datetime as dt

import numpy as np
import pandas as pd
import pytest

from fred_lx.storage.postgres_store import read_curve_history, upsert_par_yields

pytestmark = pytest.mark.postgres


def _wide_df(date: dt.date, **maturities) -> pd.DataFrame:
    return pd.DataFrame([{"date": date, **maturities}])


def test_upsert_and_read_round_trip(pg_conn):
    date = dt.date(2025, 1, 2)
    df = _wide_df(date, BC_1YEAR=4.16, BC_10YEAR=4.57)

    written = upsert_par_yields(pg_conn, df, source="test")
    assert written == 2

    history = read_curve_history(pg_conn, start=date, end=date, source="test")
    assert len(history) == 2
    by_code = history.set_index("maturity_code")["par_yield"].astype(float)
    assert by_code["BC_1YEAR"] == pytest.approx(4.16)
    assert by_code["BC_10YEAR"] == pytest.approx(4.57)


def test_upsert_overwrites_on_conflict(pg_conn):
    date = dt.date(2025, 1, 2)
    upsert_par_yields(pg_conn, _wide_df(date, BC_10YEAR=4.57), source="test")
    upsert_par_yields(pg_conn, _wide_df(date, BC_10YEAR=4.99), source="test")

    history = read_curve_history(pg_conn, start=date, end=date, source="test")
    assert len(history) == 1
    assert float(history.iloc[0]["par_yield"]) == pytest.approx(4.99)


def test_upsert_skips_nan_values(pg_conn):
    date = dt.date(2025, 1, 2)
    df = _wide_df(date, BC_1YEAR=4.16, BC_4MONTH=np.nan)

    written = upsert_par_yields(pg_conn, df, source="test")
    assert written == 1

    history = read_curve_history(pg_conn, start=date, end=date, source="test")
    assert list(history["maturity_code"]) == ["BC_1YEAR"]


def test_upsert_empty_dataframe_returns_zero(pg_conn):
    assert upsert_par_yields(pg_conn, pd.DataFrame(), source="test") == 0


def test_read_curve_history_filters_by_source(pg_conn):
    date = dt.date(2025, 1, 2)
    upsert_par_yields(pg_conn, _wide_df(date, BC_10YEAR=4.57), source="test")

    other_source = read_curve_history(pg_conn, start=date, end=date, source="not_test")
    assert other_source.empty


def test_read_curve_history_respects_date_range(pg_conn):
    upsert_par_yields(pg_conn, _wide_df(dt.date(2025, 1, 2), BC_10YEAR=4.57), source="test")
    upsert_par_yields(pg_conn, _wide_df(dt.date(2025, 1, 3), BC_10YEAR=4.56), source="test")

    history = read_curve_history(
        pg_conn, start=dt.date(2025, 1, 3), end=dt.date(2025, 1, 3), source="test"
    )
    assert len(history) == 1
    assert history.iloc[0]["date"] == dt.date(2025, 1, 3)
