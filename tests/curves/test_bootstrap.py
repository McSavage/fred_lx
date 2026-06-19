import datetime as dt

import pandas as pd
import pytest

from fred_lx.curves.bootstrap import par_to_zero

AS_OF = dt.date(2025, 1, 2)


def test_short_term_zero_equals_par():
    curve = pd.DataFrame(
        {"maturity_years": [1 / 12, 0.5, 1.0], "par_yield": [4.5, 4.4, 4.3]}
    )
    result = par_to_zero(curve, as_of=AS_OF)
    assert list(result["zero_coupon_yield"]) == pytest.approx([4.5, 4.4, 4.3])


def test_flat_par_curve_bootstraps_to_flat_zero_curve():
    # If every maturity prices at the same coupon rate, the no-arbitrage
    # zero curve must be flat at that same rate too.
    curve = pd.DataFrame(
        {"maturity_years": [0.5, 1.0, 2.0, 3.0], "par_yield": [4.0, 4.0, 4.0, 4.0]}
    )
    result = par_to_zero(curve, as_of=AS_OF)
    assert result["zero_coupon_yield"].tolist() == pytest.approx(
        [4.0, 4.0, 4.0, 4.0], abs=0.01
    )


def test_upward_sloping_curve_prices_bond_at_par():
    # The bootstrapped zero rate must reprice the long-end par bond back to
    # ~100, given the (flat, short-term) zero rates beneath it.
    curve = pd.DataFrame({"maturity_years": [0.5, 1.0, 2.0], "par_yield": [2.0, 2.0, 5.0]})
    result = par_to_zero(curve, as_of=AS_OF)

    z_short = 0.02  # short-term zero == par, from the curve above
    z_long = result.loc[2, "zero_coupon_yield"] / 100
    coupon = 0.05 / 2 * 100  # semi-annual coupon on the 2Y, 5% par bond

    price = (
        coupon / (1 + z_short / 2) ** 1
        + coupon / (1 + z_short / 2) ** 2
        + coupon / (1 + z_long / 2) ** 3
        + (coupon + 100) / (1 + z_long / 2) ** 4
    )
    # Looser tolerance than a pure formula check: QuantLib reprices against
    # real calendar/day-count dates rather than idealized 0.5Y periods.
    assert price == pytest.approx(100.0, abs=0.1)


def test_single_long_maturity_with_no_shorter_data():
    # A long-term maturity with nothing shorter than it to bootstrap from.
    curve = pd.DataFrame({"maturity_years": [2.0], "par_yield": [4.0]})
    result = par_to_zero(curve, as_of=AS_OF)
    assert result["zero_coupon_yield"].iloc[0] == pytest.approx(4.0, abs=0.01)


def test_as_of_defaults_to_max_curve_date():
    curve = pd.DataFrame(
        {
            "maturity_years": [0.5, 1.0],
            "par_yield": [4.0, 4.0],
            "date": [dt.date(2025, 1, 2), dt.date(2025, 1, 3)],
        }
    )
    # Should not raise without an explicit as_of, and should still bootstrap.
    result = par_to_zero(curve)
    assert result["zero_coupon_yield"].tolist() == pytest.approx([4.0, 4.0])
