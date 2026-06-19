"""Plotting helpers for forward-rate analysis."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def plot_forward_rates(forward_df: pd.DataFrame, yield_df: pd.DataFrame) -> plt.Figure:
    """Plot implied forward rates and overlay them against current spot rates.

    Args:
        forward_df: As returned by ``fred_lx.curves.forwards.forward_rates``.
        yield_df: Curve with ``maturity_years`` and ``zero_coupon_yield``.
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))

    x_pos = range(len(forward_df))
    ax1.bar(x_pos, forward_df["forward_rate"], alpha=0.7, color="orange")

    for i, (_, row) in enumerate(forward_df.iterrows()):
        ax1.annotate(
            f"{row['forward_rate']:.2f}%",
            (i, row["forward_rate"]),
            textcoords="offset points",
            xytext=(0, 5),
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
        )

    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(forward_df["period"], rotation=45)
    ax1.set_ylabel("Forward Rate (%)", fontsize=12, fontweight="bold")
    ax1.set_title("Implied Forward Rates", fontsize=14, fontweight="bold")
    ax1.grid(True, alpha=0.3)

    ax2.plot(
        yield_df["maturity_years"],
        yield_df["zero_coupon_yield"],
        marker="o",
        linewidth=3,
        markersize=8,
        color="darkred",
        alpha=0.8,
        label="Current Spot Rates",
    )

    for idx, row in forward_df.iterrows():
        mid_point = (row["start_year"] + row["end_year"]) / 2
        ax2.scatter(
            mid_point,
            row["forward_rate"],
            s=100,
            color="orange",
            alpha=0.8,
            marker="^",
            label="Forward Rates" if idx == 0 else "",
        )
        ax2.annotate(
            f"{row['period']}\n{row['forward_rate']:.2f}%",
            (mid_point, row["forward_rate"]),
            textcoords="offset points",
            xytext=(0, 15),
            ha="center",
            va="bottom",
            fontsize=8,
        )

    ax2.set_xlabel("Years to Maturity", fontsize=12, fontweight="bold")
    ax2.set_ylabel("Rate (%)", fontsize=12, fontweight="bold")
    ax2.set_title("Forward Rates vs Current Spot Rates", fontsize=12, fontweight="bold")
    ax2.grid(True, alpha=0.3)
    ax2.legend()

    plt.tight_layout()
    return fig


def create_summary_table(yield_df: pd.DataFrame, forward_df: pd.DataFrame) -> plt.Figure:
    """Render a two-panel summary table: the yield curve, then forward rates.

    Args:
        yield_df: Curve with ``maturity_label``, ``par_yield``,
            ``maturity_years``, and optionally ``zero_coupon_yield``.
        forward_df: As returned by ``fred_lx.curves.forwards.forward_rates``.
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))

    ax1.axis("tight")
    ax1.axis("off")

    table_data = []
    for _, row in yield_df.iterrows():
        zero_coupon = row.get("zero_coupon_yield", np.nan)
        spread = zero_coupon - row["par_yield"] if not pd.isna(zero_coupon) else np.nan

        table_data.append(
            [
                row["maturity_label"],
                f"{row['par_yield']:.3f}%",
                f"{zero_coupon:.3f}%" if not pd.isna(zero_coupon) else "N/A",
                f"{spread:.3f}" if not pd.isna(spread) else "N/A",
                f"{row['maturity_years']:.2f}",
            ]
        )

    table1 = ax1.table(
        cellText=table_data,
        colLabels=["Maturity", "Par Yield", "Zero-Coupon", "Spread (bps)", "Years"],
        cellLoc="center",
        loc="center",
        bbox=[0, 0, 1, 1],
    )
    table1.auto_set_font_size(False)
    table1.set_fontsize(10)
    table1.scale(1.2, 2)

    for i in range(len(yield_df) + 1):
        for j in range(5):
            cell = table1[(i, j)]
            if i == 0:
                cell.set_facecolor("#4472C4")
                cell.set_text_props(weight="bold", color="white")
            else:
                cell.set_facecolor("#F2F2F2" if i % 2 == 0 else "white")

    ax1.set_title("Treasury Yield Curve Summary", fontsize=14, fontweight="bold", pad=20)

    if not forward_df.empty:
        ax2.axis("tight")
        ax2.axis("off")

        forward_table_data = [
            [
                row["period"],
                f"{row['forward_rate']:.3f}%",
                f"{row['start_spot_rate']:.3f}%",
                f"{row['end_spot_rate']:.3f}%",
            ]
            for _, row in forward_df.iterrows()
        ]

        table2 = ax2.table(
            cellText=forward_table_data,
            colLabels=["Period", "Forward Rate", "Start Spot", "End Spot"],
            cellLoc="center",
            loc="center",
            bbox=[0, 0, 1, 1],
        )
        table2.auto_set_font_size(False)
        table2.set_fontsize(10)
        table2.scale(1.2, 2)

        for i in range(len(forward_df) + 1):
            for j in range(4):
                cell = table2[(i, j)]
                if i == 0:
                    cell.set_facecolor("#C5504B")
                    cell.set_text_props(weight="bold", color="white")
                else:
                    cell.set_facecolor("#FFE6E6" if i % 2 == 0 else "white")

        ax2.set_title("Forward Rates Analysis", fontsize=14, fontweight="bold", pad=20)
    else:
        ax2.text(
            0.5,
            0.5,
            "No forward rates calculated",
            ha="center",
            va="center",
            fontsize=14,
            transform=ax2.transAxes,
        )
        ax2.set_title("Forward Rates Analysis", fontsize=14, fontweight="bold", pad=20)

    plt.tight_layout()
    return fig
