import datetime as dt

import matplotlib

matplotlib.use("Agg")

import pandas as pd
import pytest

from fred_lx.viz.curves import plot_yield_curves


@pytest.fixture
def curve() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "maturity_label": ["1M", "1Y", "10Y"],
            "maturity_years": [1 / 12, 1.0, 10.0],
            "par_yield": [4.37, 4.16, 4.57],
            "zero_coupon_yield": [4.37, 4.16, 4.6],
            "date": [dt.date(2025, 1, 2)] * 3,
        }
    )


def test_plot_yield_curves_renders_with_zero_coupon_column(curve):
    fig = plot_yield_curves(curve)
    assert len(fig.axes) == 2


def test_plot_yield_curves_renders_without_zero_coupon_column(curve):
    fig = plot_yield_curves(curve.drop(columns=["zero_coupon_yield"]))
    assert len(fig.axes) == 2
