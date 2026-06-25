"""PCA factor analysis of the Treasury yield curve.

PCA runs on day-over-day yield *changes*, not yield levels. This is the
standard Litterman-Scheinkman approach to extracting level/slope/curvature
factors from yield curve history, and it's also the representation a future
risk module (VaR, scenario shocks) needs -- those work in terms of how much
the curve moves, not where it sits. See docs/refactor-plan.md section 8.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class PCAResult:
    """Result of fitting PCA to yield curve changes.

    Attributes:
        maturities: Maturity years, in the same order as ``components``'
            columns.
        components: Principal axes, shape ``(n_components, n_maturities)``.
            Row 0 is typically a "level" factor (same sign across
            maturities), row 1 "slope", row 2 "curvature".
        explained_variance_ratio: Fraction of total variance in yield
            changes explained by each component, shape ``(n_components,)``.
        scores: Factor time series, index = date, columns ``PC1..PCn``.
        variance_table: Per-maturity variance decomposition, as in
            Litterman & Scheinkman (1991) Table 2. Index = maturity_years,
            columns ``total_explained_pct`` (share of that maturity's own
            variance explained by the kept components) and ``PC1..PCn``
            (share of *that explained variance* attributable to each
            component; the PC columns sum to 100 per row).
    """

    maturities: np.ndarray
    components: np.ndarray
    explained_variance_ratio: np.ndarray
    scores: pd.DataFrame
    variance_table: pd.DataFrame


def fit_yield_pca(history: pd.DataFrame, n_components: int = 3, c_start: int = 0) -> PCAResult:
    """Fit PCA factors to historical yield curve changes.

    Args:
        history: Long-format DataFrame with ``date``, ``maturity_years``,
            and ``par_yield`` columns, e.g. as returned by
            ``postgres_store.read_curve_history`` or an equivalent DuckDB
            query against ``pg.treasury_par_yields``.
        n_components: Number of principal components to keep.

    Returns:
        A ``PCAResult`` with components, explained variance, and the factor
        score time series.
    """
    wide = history.pivot(
        index="date", columns="maturity_years", values="par_yield"
    ).sort_index(axis=1)
    wide = wide.dropna(axis=0, how="any")
    wide = wide.iloc[:, c_start:]  # option drop the first columns based on c_start

    diffs = wide.diff().dropna(axis=0, how="any")
    mean = diffs.mean(axis=0)
    centered = diffs - mean

    n_obs = centered.shape[0]
    _, singular_values, vt = np.linalg.svd(centered.to_numpy(), full_matrices=False)

    variance = singular_values**2 / (n_obs - 1)
    explained_variance_ratio = variance[:n_components] / variance.sum()

    components = vt[:n_components].copy()
    scores = centered.to_numpy() @ components.T

    for i in range(n_components):
        if components[i].sum() < 0:
            components[i] *= -1
            scores[:, i] *= -1

    scores_df = pd.DataFrame(
        scores,
        index=centered.index,
        columns=[f"PC{i + 1}" for i in range(n_components)],
    )

    # Litterman-Scheinkman Table 2: per-maturity variance explained by each
    # kept component, as a share of that maturity's own variance.
    eigenvalues = variance[:n_components]
    factor_variance = eigenvalues[:, np.newaxis] * components**2
    total_explained = factor_variance.sum(axis=0)
    total_variance = centered.var(axis=0, ddof=1).to_numpy()

    variance_table = pd.DataFrame(
        (factor_variance / total_explained * 100).T,
        index=pd.Index(wide.columns, name="maturity_years"),
        columns=[f"PC{i + 1}" for i in range(n_components)],
    )
    variance_table.insert(0, "total_explained_pct", total_explained / total_variance * 100)

    return PCAResult(
        maturities=wide.columns.to_numpy(dtype=float),
        components=components,
        explained_variance_ratio=explained_variance_ratio,
        scores=scores_df,
        variance_table=variance_table,
    )
