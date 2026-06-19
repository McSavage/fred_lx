"""Par yield -> zero-coupon (spot) yield bootstrapping via QuantLib.

Short-end (<=1Y) maturities are modeled as money-market deposits, longer
maturities as semiannual bullet bonds priced at par, and QuantLib's
PiecewiseLogCubicDiscount solves the whole no-arbitrage discount curve at
once. See docs/refactor-plan.md section 9, step 4.
"""

import datetime as dt

import pandas as pd
import QuantLib as ql

SETTLEMENT_DAYS = 0
CALENDAR = ql.NullCalendar()
BOND_DAY_COUNT = ql.ActualActual(ql.ActualActual.ISMA)
DEPOSIT_DAY_COUNT = ql.Actual360()


def par_to_zero(curve: pd.DataFrame, as_of: dt.date | None = None) -> pd.DataFrame:
    """Bootstrap zero-coupon yields from a par yield curve using QuantLib.

    Args:
        curve: DataFrame with ``maturity_years`` and ``par_yield`` columns.
        as_of: Curve date, used as the bootstrap's evaluation date. Defaults
            to ``curve['date'].max()`` if present, otherwise today.

    Returns:
        Copy of ``curve`` with a ``zero_coupon_yield`` column added.
    """
    if as_of is None:
        as_of = curve["date"].max() if "date" in curve.columns else dt.date.today()

    eval_date = ql.Date(as_of.day, as_of.month, as_of.year)
    ql.Settings.instance().evaluationDate = eval_date

    sorted_curve = curve.sort_values("maturity_years")
    helpers = [
        _rate_helper(eval_date, row.maturity_years, row.par_yield)
        for row in sorted_curve.itertuples()
    ]

    term_structure = ql.PiecewiseLogCubicDiscount(eval_date, helpers, BOND_DAY_COUNT)
    term_structure.enableExtrapolation()

    df = curve.copy()
    df["zero_coupon_yield"] = [
        # <=1Y deposit quotes are simple/Act-360; reporting them through the
        # semiannual-compounded zeroRate() call below would introduce a pure
        # compounding-convention artifact rather than a real bootstrap
        # result, so pass them through as-is.
        par_yield if maturity_years <= 1.0 else _zero_rate(term_structure, eval_date, maturity_years)
        for maturity_years, par_yield in zip(df["maturity_years"], df["par_yield"])
    ]
    return df


def _rate_helper(eval_date: ql.Date, maturity_years: float, par_yield: float) -> ql.RateHelper:
    months = round(maturity_years * 12)

    if maturity_years <= 1.0:
        return ql.DepositRateHelper(
            par_yield / 100,
            ql.Period(months, ql.Months),
            SETTLEMENT_DAYS,
            CALENDAR,
            ql.ModifiedFollowing,
            False,
            DEPOSIT_DAY_COUNT,
        )

    schedule = ql.Schedule(
        eval_date,
        eval_date + ql.Period(months, ql.Months),
        ql.Period(ql.Semiannual),
        CALENDAR,
        ql.Unadjusted,
        ql.Unadjusted,
        ql.DateGeneration.Backward,
        False,
    )
    return ql.FixedRateBondHelper(
        ql.QuoteHandle(ql.SimpleQuote(100.0)),
        SETTLEMENT_DAYS,
        100.0,
        schedule,
        [par_yield / 100],
        BOND_DAY_COUNT,
        ql.Unadjusted,
        100.0,
    )


def _zero_rate(
    term_structure: ql.YieldTermStructure, eval_date: ql.Date, maturity_years: float
) -> float:
    target_date = eval_date + ql.Period(round(maturity_years * 12), ql.Months)
    zero = term_structure.zeroRate(
        target_date, BOND_DAY_COUNT, ql.Compounded, ql.Semiannual
    )
    return zero.rate() * 100
