import pandas as pd
import pytest

from fred_lx.curves.forwards import forward_rates


def test_flat_zero_curve_implies_flat_forward_rates():
    curve = pd.DataFrame(
        {
            "maturity_years": [1, 2, 3, 5, 7, 10, 20, 30],
            "zero_coupon_yield": [4.0] * 8,
        }
    )
    result = forward_rates(curve)
    assert result["forward_rate"].tolist() == pytest.approx([4.0] * len(result), abs=1e-6)


def test_forward_rate_matches_closed_form():
    curve = pd.DataFrame({"maturity_years": [5, 7], "zero_coupon_yield": [3.0, 5.0]})
    result = forward_rates(curve, periods=[(5, 7)])

    z1, z2 = 0.03, 0.05
    expected_forward = ((1 + z2) ** 7 / (1 + z1) ** 5) ** (1 / 2) - 1

    assert len(result) == 1
    row = result.iloc[0]
    assert row["period"] == "5Y-7Y"
    assert row["forward_rate"] == pytest.approx(expected_forward * 100)
    assert row["start_spot_rate"] == pytest.approx(3.0)
    assert row["end_spot_rate"] == pytest.approx(5.0)


def test_periods_beyond_max_maturity_are_skipped():
    curve = pd.DataFrame({"maturity_years": [1, 2], "zero_coupon_yield": [4.0, 4.2]})
    result = forward_rates(curve, periods=[(1, 2), (10, 20)])
    assert list(result["period"]) == ["1Y-2Y"]


def test_insufficient_data_returns_empty():
    curve = pd.DataFrame({"maturity_years": [1], "zero_coupon_yield": [4.0]})
    result = forward_rates(curve)
    assert result.empty
