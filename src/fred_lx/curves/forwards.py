"""Forward rate calculations from a zero-coupon yield curve."""

import pandas as pd
from scipy.interpolate import interp1d

DEFAULT_FORWARD_PERIODS: list[tuple[float, float]] = [
    (1, 2),
    (2, 3),
    (3, 5),
    (5, 7),
    (7, 10),
    (10, 20),
    (20, 30),
]


def forward_rates(
    curve: pd.DataFrame,
    periods: list[tuple[float, float]] | None = None,
) -> pd.DataFrame:
    """Compute implied forward rates between pairs of maturities.

    Args:
        curve: DataFrame with ``maturity_years`` and ``zero_coupon_yield``
            columns (as returned by ``fred_lx.curves.bootstrap.par_to_zero``).
        periods: ``(start_year, end_year)`` pairs to compute forwards for.
            Defaults to ``DEFAULT_FORWARD_PERIODS``.

    Returns:
        DataFrame with one row per period: ``period``, ``start_year``,
        ``end_year``, ``forward_rate``, ``start_spot_rate``, ``end_spot_rate``.
        Empty if there isn't enough data to interpolate.
    """
    if periods is None:
        periods = DEFAULT_FORWARD_PERIODS

    valid = curve.dropna(subset=["zero_coupon_yield"])
    if len(valid) < 2:
        return pd.DataFrame()

    interp = interp1d(
        valid["maturity_years"],
        valid["zero_coupon_yield"],
        kind="linear",
        fill_value="extrapolate",
    )

    max_maturity = valid["maturity_years"].max()
    records = []
    for start_year, end_year in periods:
        if start_year > max_maturity or end_year > max_maturity:
            continue

        z1 = interp(start_year) / 100
        z2 = interp(end_year) / 100
        forward_rate = (
            (1 + z2) ** end_year / (1 + z1) ** start_year
        ) ** (1 / (end_year - start_year)) - 1

        records.append(
            {
                "period": f"{int(start_year)}Y-{int(end_year)}Y",
                "start_year": start_year,
                "end_year": end_year,
                "forward_rate": forward_rate * 100,
                "start_spot_rate": z1 * 100,
                "end_spot_rate": z2 * 100,
            }
        )

    return pd.DataFrame(records)
