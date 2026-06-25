import matplotlib

matplotlib.use("Agg")

import numpy as np
import pandas as pd
import pytest

from fred_lx.analysis.pca import PCAResult
from fred_lx.viz.pca import plot_components, plot_explained_variance, plot_scores


@pytest.fixture
def result() -> PCAResult:
    dates = pd.date_range("2025-01-02", periods=5, freq="B")
    return PCAResult(
        maturities=np.array([1.0, 2.0, 5.0, 10.0]),
        components=np.array(
            [[0.5, 0.5, 0.5, 0.5], [-0.6, -0.2, 0.2, 0.6]]
        ),
        explained_variance_ratio=np.array([0.8, 0.15]),
        scores=pd.DataFrame(
            {"PC1": [0.1, -0.2, 0.3, 0.0, -0.1], "PC2": [0.0, 0.1, -0.1, 0.2, 0.0]},
            index=dates,
        ),
        variance_table=pd.DataFrame(
            {
                "total_explained_pct": [95.0, 96.0, 97.0, 98.0],
                "PC1": [80.0, 82.0, 84.0, 86.0],
                "PC2": [20.0, 18.0, 16.0, 14.0],
            },
            index=pd.Index([1.0, 2.0, 5.0, 10.0], name="maturity_years"),
        ),
    )


def test_plot_components_renders_one_axis(result):
    fig = plot_components(result)
    assert len(fig.axes) == 1


def test_plot_explained_variance_renders_one_axis(result):
    fig = plot_explained_variance(result)
    assert len(fig.axes) == 1


def test_plot_scores_renders_one_axis(result):
    fig = plot_scores(result)
    assert len(fig.axes) == 1
