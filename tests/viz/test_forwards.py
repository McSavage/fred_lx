import datetime as dt

import matplotlib

matplotlib.use("Agg")

import pandas as pd
import pytest

from fred_lx.viz.forwards import create_summary_table, plot_forward_rates


@pytest.fixture
def curve() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "maturity_label": ["1Y", "2Y", "10Y"],
            "maturity_years": [1.0, 2.0, 10.0],
            "par_yield": [4.16, 4.25, 4.57],
            "zero_coupon_yield": [4.16, 4.26, 4.6],
            "date": [dt.date(2025, 1, 2)] * 3,
        }
    )


@pytest.fixture
def forward_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "period": ["1Y-2Y", "2Y-10Y"],
            "start_year": [1, 2],
            "end_year": [2, 10],
            "forward_rate": [4.3, 4.7],
            "start_spot_rate": [4.16, 4.26],
            "end_spot_rate": [4.26, 4.6],
        }
    )


def test_plot_forward_rates_renders(curve, forward_df):
    fig = plot_forward_rates(forward_df, curve)
    assert len(fig.axes) == 2


def test_create_summary_table_renders_with_forwards(curve, forward_df):
    fig = create_summary_table(curve, forward_df)
    assert len(fig.axes) == 2


def test_create_summary_table_renders_with_empty_forwards(curve):
    fig = create_summary_table(curve, pd.DataFrame())
    assert len(fig.axes) == 2
