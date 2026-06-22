"""Plotting helpers for yield curve PCA results."""

import matplotlib.pyplot as plt

from fred_lx.analysis.pca import PCAResult


def plot_components(result: PCAResult) -> plt.Figure:
    """Plot each component's loading across maturities (the factor shapes)."""
    fig, ax = plt.subplots(figsize=(10, 6))

    for i, loadings in enumerate(result.components):
        ax.plot(result.maturities, loadings, marker="o", linewidth=2, label=f"PC{i + 1}")

    ax.axhline(y=0, color="black", linestyle="-", alpha=0.3)
    ax.set_xlabel("Years to Maturity", fontsize=12, fontweight="bold")
    ax.set_ylabel("Loading", fontsize=12, fontweight="bold")
    ax.set_title("Yield Curve PCA: Component Loadings", fontsize=14, fontweight="bold")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10)

    return fig


def plot_explained_variance(result: PCAResult) -> plt.Figure:
    """Plot a scree chart of variance explained by each component."""
    fig, ax = plt.subplots(figsize=(8, 5))

    labels = [f"PC{i + 1}" for i in range(len(result.explained_variance_ratio))]
    ax.bar(labels, result.explained_variance_ratio * 100, color="navy", alpha=0.8)

    for i, ratio in enumerate(result.explained_variance_ratio):
        ax.annotate(
            f"{ratio * 100:.1f}%",
            (i, ratio * 100),
            textcoords="offset points",
            xytext=(0, 5),
            ha="center",
            fontsize=10,
        )

    ax.set_ylabel("Explained Variance (%)", fontsize=12, fontweight="bold")
    ax.set_title("Yield Curve PCA: Explained Variance", fontsize=14, fontweight="bold")
    ax.grid(True, alpha=0.3, axis="y")

    return fig


def plot_scores(result: PCAResult) -> plt.Figure:
    """Plot the factor score time series."""
    fig, ax = plt.subplots(figsize=(12, 6))

    for column in result.scores.columns:
        ax.plot(result.scores.index, result.scores[column], linewidth=1.5, label=column)

    ax.axhline(y=0, color="black", linestyle="-", alpha=0.3)
    ax.set_xlabel("Date", fontsize=12, fontweight="bold")
    ax.set_ylabel("Factor Score", fontsize=12, fontweight="bold")
    ax.set_title("Yield Curve PCA: Factor Scores Over Time", fontsize=14, fontweight="bold")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10)

    return fig
