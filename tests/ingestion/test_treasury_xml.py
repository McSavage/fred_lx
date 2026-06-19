from datetime import date, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests

from fred_lx.ingestion.treasury_xml import (
    TREASURY_XML_URL,
    fetch_treasury_xml,
    parse_par_yields,
)

FIXTURE = Path(__file__).parent.parent / "fixtures" / "treasury_sample.xml"


def test_parse_par_yields_shape_and_dates():
    xml_data = FIXTURE.read_text()
    df = parse_par_yields(xml_data)

    assert len(df) == 2
    assert df["date"].min() == date(2025, 1, 2)
    assert df["date"].max() == date(2025, 1, 3)
    # Sorted ascending by date.
    assert list(df["date"]) == sorted(df["date"])


def test_parse_par_yields_values_and_missing_fields():
    xml_data = FIXTURE.read_text()
    df = parse_par_yields(xml_data)

    first = df.iloc[0]
    assert first["BC_10YEAR"] == 4.57
    assert first["BC_1MONTH"] == 4.37
    # BC_4MONTH is present but empty in the fixture -> NaN, not dropped.
    assert pd.isna(first["BC_4MONTH"])


def test_parse_par_yields_empty_feed():
    empty_feed = (
        '<feed xmlns="http://www.w3.org/2005/Atom" '
        'xmlns:d="http://schemas.microsoft.com/ado/2007/08/dataservices" '
        'xmlns:m="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata">'
        "</feed>"
    )
    df = parse_par_yields(empty_feed)
    assert df.empty


@patch("fred_lx.ingestion.treasury_xml.requests.get")
def test_fetch_treasury_xml_builds_correct_request(mock_get):
    mock_response = MagicMock()
    mock_response.text = "<feed></feed>"
    mock_get.return_value = mock_response

    result = fetch_treasury_xml(year=2024)

    mock_get.assert_called_once_with(
        TREASURY_XML_URL,
        params={"data": "daily_treasury_yield_curve", "field_tdr_date_value": "2024"},
        timeout=30,
    )
    mock_response.raise_for_status.assert_called_once()
    assert result == "<feed></feed>"


@patch("fred_lx.ingestion.treasury_xml.requests.get")
def test_fetch_treasury_xml_defaults_to_current_year(mock_get):
    mock_response = MagicMock()
    mock_response.text = "<feed></feed>"
    mock_get.return_value = mock_response

    fetch_treasury_xml()

    sent_params = mock_get.call_args.kwargs["params"]
    assert sent_params["field_tdr_date_value"] == str(datetime.now().year)


@patch("fred_lx.ingestion.treasury_xml.requests.get")
def test_fetch_treasury_xml_propagates_http_errors(mock_get):
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.HTTPError("503 error")
    mock_get.return_value = mock_response

    with pytest.raises(requests.HTTPError):
        fetch_treasury_xml(year=2024)


@patch("fred_lx.ingestion.treasury_xml.requests.get")
def test_fetch_treasury_xml_passes_custom_timeout(mock_get):
    mock_response = MagicMock()
    mock_response.text = "<feed></feed>"
    mock_get.return_value = mock_response

    fetch_treasury_xml(year=2024, timeout=5)

    assert mock_get.call_args.kwargs["timeout"] == 5
