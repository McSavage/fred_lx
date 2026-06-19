"""Plotting helpers for par / zero-coupon yield curves."""

import matplotlib.pyplot as plt
import pandas as pd


def plot_yield_curves(df: pd.DataFrame, title_suffix: str = "") -> plt.Figure:
    """Plot par yields and, if present, zero-coupon yields with their spread.

    Args:
        df: Curve with ``maturity_years``, ``maturity_label``, ``par_yield``,
            ``date``, and optionally ``zero_coupon_yield`` columns.
        title_suffix: Appended to the plot title.
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12))

    ax1.plot(
        df["maturity_years"],
        df["par_yield"],
        marker="o",
        linewidth=3,
        markersize=8,
        color="navy",
        alpha=0.8,
        label="Par Yield Curve",
    )

    if "zero_coupon_yield" in df.columns:
        ax1.plot(
            df["maturity_years"],
            df["zero_coupon_yield"],
            marker="s",
            linewidth=3,
            markersize=8,
            color="darkred",
            alpha=0.8,
            label="Zero-Coupon Yield Curve",
        )

    for _, row in df.iterrows():
        ax1.annotate(
            f"{row['maturity_label']}\n{row['par_yield']:.2f}%",
            (row["maturity_years"], row["par_yield"]),
            textcoords="offset points",
            xytext=(0, 15),
            ha="center",
            va="bottom",
            fontsize=9,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.7),
        )

    ax1.set_xlabel("Years to Maturity", fontsize=12, fontweight="bold")
    ax1.set_ylabel("Yield (%)", fontsize=12, fontweight="bold")
    ax1.set_title(
        f"US Treasury Par Yield Curve vs Zero-Coupon Curve{title_suffix}\n"
        f"Data as of: {df['date'].iloc[0]}",
        fontsize=14,
        fontweight="bold",
        pad=20,
    )
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=10)

    if "zero_coupon_yield" in df.columns:
        spread = df["zero_coupon_yield"] - df["par_yield"]
        ax2.bar(df["maturity_years"], spread, alpha=0.6, color="green", width=0.8)

        for _, row in df.iterrows():
            spread_val = row["zero_coupon_yield"] - row["par_yield"]
            ax2.annotate(
                f"{spread_val:.2f}",
                (row["maturity_years"], spread_val),
                textcoords="offset points",
                xytext=(0, 5 if spread_val >= 0 else -15),
                ha="center",
                va="bottom" if spread_val >= 0 else "top",
                fontsize=9,
            )

        ax2.axhline(y=0, color="black", linestyle="-", alpha=0.5)
        ax2.set_xlabel("Years to Maturity", fontsize=12, fontweight="bold")
        ax2.set_ylabel("Spread (bps)", fontsize=12, fontweight="bold")
        ax2.set_title("Zero-Coupon vs Par Yield Spread", fontsize=12, fontweight="bold")
        ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig
