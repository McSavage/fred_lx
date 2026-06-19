"""Shared constants and helpers for the Treasury par yield curve."""

import pandas as pd

# Treasury XML field name -> years to maturity.
MATURITY_MAPPING: dict[str, float] = {
    "BC_1MONTH": 1 / 12,
    "BC_2MONTH": 2 / 12,
    "BC_3MONTH": 3 / 12,
    "BC_4MONTH": 4 / 12,
    "BC_6MONTH": 6 / 12,
    "BC_1YEAR": 1,
    "BC_2YEAR": 2,
    "BC_3YEAR": 3,
    "BC_5YEAR": 5,
    "BC_7YEAR": 7,
    "BC_10YEAR": 10,
    "BC_20YEAR": 20,
    "BC_30YEAR": 30,
}

MATURITY_LABELS: dict[str, str] = {
    "BC_1MONTH": "1M",
    "BC_2MONTH": "2M",
    "BC_3MONTH": "3M",
    "BC_4MONTH": "4M",
    "BC_6MONTH": "6M",
    "BC_1YEAR": "1Y",
    "BC_2YEAR": "2Y",
    "BC_3YEAR": "3Y",
    "BC_5YEAR": "5Y",
    "BC_7YEAR": "7Y",
    "BC_10YEAR": "10Y",
    "BC_20YEAR": "20Y",
    "BC_30YEAR": "30Y",
}


def latest_curve(df: pd.DataFrame) -> pd.DataFrame:
    """Extract the most recent complete par yield curve from a history DataFrame.

    Args:
        df: Wide DataFrame as returned by
            ``fred_lx.ingestion.treasury_xml.parse_par_yields`` — one row per
            date, one column per ``BC_*`` maturity code.

    Returns:
        Long DataFrame with one row per maturity: ``maturity_code``,
        ``maturity_label``, ``maturity_years``, ``par_yield``, ``date``.
    """
    if df.empty:
        return pd.DataFrame()

    latest_date = df["date"].max()
    latest_row = df[df["date"] == latest_date].iloc[0]

    records = [
        {
            "maturity_code": code,
            "maturity_label": MATURITY_LABELS[code],
            "maturity_years": years,
            "par_yield": latest_row[code],
            "date": latest_date,
        }
        for code, years in MATURITY_MAPPING.items()
        if code in latest_row and not pd.isna(latest_row[code])
    ]

    curve = pd.DataFrame(records)
    return curve.sort_values("maturity_years").reset_index(drop=True)
