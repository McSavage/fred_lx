import numpy as np
import pandas as pd

from fred_lx.analysis.pca import fit_yield_pca

MATURITIES = np.array([1.0, 2.0, 5.0, 10.0, 30.0])


def _synthetic_history(n_days: int = 200, seed: int = 0) -> pd.DataFrame:
    """Build yield levels driven by a dominant parallel ("level") shock plus
    a smaller maturity-dependent ("slope") shock, so PCA has a known answer
    to recover: PC1 should be level (uniform sign, dominant variance), and
    PC1's variance share should exceed PC2's.
    """
    rng = np.random.default_rng(seed)

    level_shock = rng.normal(0, 1.0, n_days)
    slope_weight = (MATURITIES - MATURITIES.mean()) / MATURITIES.std()
    slope_shock = rng.normal(0, 0.3, n_days)
    noise = rng.normal(0, 0.01, (n_days, len(MATURITIES)))

    diffs = np.outer(level_shock, np.ones_like(MATURITIES)) + np.outer(
        slope_shock, slope_weight
    ) + noise
    levels = 4.0 + np.cumsum(diffs, axis=0)

    dates = pd.date_range("2025-01-02", periods=n_days, freq="B")
    wide = pd.DataFrame(levels, index=dates, columns=MATURITIES)
    long = wide.reset_index(names="date").melt(
        id_vars="date", var_name="maturity_years", value_name="par_yield"
    )
    return long


def test_pc1_dominates_variance_and_is_a_level_factor():
    history = _synthetic_history()
    result = fit_yield_pca(history, n_components=2)

    assert result.explained_variance_ratio[0] > result.explained_variance_ratio[1]
    # A level shock moves every maturity the same direction.
    assert np.all(result.components[0] > 0)


def test_shapes_match_requested_n_components():
    history = _synthetic_history()
    result = fit_yield_pca(history, n_components=3)

    assert result.components.shape == (3, len(MATURITIES))
    assert result.explained_variance_ratio.shape == (3,)
    assert list(result.scores.columns) == ["PC1", "PC2", "PC3"]
    assert np.array_equal(result.maturities, np.sort(MATURITIES))


def test_explained_variance_ratios_are_fractions_of_total():
    history = _synthetic_history()
    result = fit_yield_pca(history, n_components=len(MATURITIES))

    assert result.explained_variance_ratio.sum() <= 1.0 + 1e-9
    assert np.all(result.explained_variance_ratio >= 0)


def test_scores_index_aligns_with_diffed_dates():
    history = _synthetic_history(n_days=50)
    result = fit_yield_pca(history, n_components=2)

    # diff() drops the first date.
    expected_dates = pd.date_range("2025-01-02", periods=50, freq="B")[1:]
    assert list(result.scores.index) == list(expected_dates)
