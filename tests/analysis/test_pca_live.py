"""Debugging entry point, not a correctness check.

Pulls real history through the same DuckDB -> Postgres path as
PCA/YieldCurvePCA.ipynb and prints the PCAResult fields, so you can attach a
debugger or eyeball real numbers (e.g. that components read as
level/slope/curvature and variance_table percentages look sane) instead of
only ever exercising fit_yield_pca against synthetic fixtures.

Run with `uv run pytest -s tests/analysis/test_pca_live.py`, or via the
"Debug fit_yield_pca on real data" launch.json config.
"""

import psycopg
import pytest

from fred_lx.analysis.pca import fit_yield_pca
from fred_lx.config import settings
from fred_lx.storage.duckdb_store import attach_postgres
from fred_lx.storage.postgres_store import connect

pytestmark = pytest.mark.postgres


def _postgres_reachable() -> bool:
    try:
        with connect():
            return True
    except psycopg.OperationalError:
        return False


def test_fit_yield_pca_smoke_on_real_history():
    if not _postgres_reachable():
        pytest.skip(f"Postgres not reachable at {settings.postgres_host}:{settings.postgres_port}")

    con = attach_postgres()
    history = con.sql("""
        SELECT curve_date AS date, maturity_years, par_yield
        FROM pg.treasury_par_yields
        WHERE source = 'treasury_xml'
    """).df()

    result = fit_yield_pca(history, n_components=3)

    print("\nmaturities:", result.maturities)
    print("explained_variance_ratio:", result.explained_variance_ratio)
    print("\nvariance_table:\n", result.variance_table)
    print("\nscores.tail():\n", result.scores.tail())

    # Cheap to assert, but the printed output above is the actual point.
    assert not result.scores.isna().any().any()
    assert result.components.shape[1] == len(result.maturities)
