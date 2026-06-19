"""Fetch and parse the US Treasury Daily Par Yield Curve XML feed."""

import xml.etree.ElementTree as ET
from datetime import datetime

import numpy as np
import pandas as pd
import requests

from fred_lx.curves.par_curve import MATURITY_MAPPING

TREASURY_XML_URL = (
    "https://home.treasury.gov/resource-center/data-chart-center/"
    "interest-rates/pages/xmlview"
)

_ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}
_PROPERTIES_TAG = (
    "{http://schemas.microsoft.com/ado/2007/08/dataservices/metadata}properties"
)
_DATASERVICES_NS = "http://schemas.microsoft.com/ado/2007/08/dataservices"


def fetch_treasury_xml(year: int | None = None, timeout: int = 30) -> str:
    """Fetch the raw Treasury par yield curve XML for a given year.

    Args:
        year: Year to fetch (defaults to the current year).
        timeout: HTTP request timeout in seconds.

    Returns:
        Raw XML response body.
    """
    if year is None:
        year = datetime.now().year

    params = {"data": "daily_treasury_yield_curve", "field_tdr_date_value": str(year)}
    response = requests.get(TREASURY_XML_URL, params=params, timeout=timeout)
    response.raise_for_status()
    return response.text


def parse_par_yields(xml_data: str) -> pd.DataFrame:
    """Parse Treasury par yield XML into a wide DataFrame.

    Args:
        xml_data: Raw XML string as returned by ``fetch_treasury_xml``.

    Returns:
        DataFrame with one row per date, one column per ``BC_*`` maturity
        code (e.g. ``BC_10YEAR``), sorted ascending by date. Empty if no
        records were found.
    """
    root = ET.fromstring(xml_data)
    entries = root.findall(".//atom:entry", _ATOM_NS)

    records = []
    for entry in entries:
        content = entry.find("atom:content", _ATOM_NS)
        if content is None:
            continue

        properties = content.find(f".//{_PROPERTIES_TAG}")
        if properties is None:
            continue

        record: dict[str, object] = {}

        date_elem = properties.find(f".//{{{_DATASERVICES_NS}}}NEW_DATE")
        if date_elem is None or not date_elem.text:
            continue
        record["date"] = pd.to_datetime(date_elem.text).date()

        for field_name in MATURITY_MAPPING:
            elem = properties.find(f".//{{{_DATASERVICES_NS}}}{field_name}")
            if elem is not None and elem.text and elem.text.strip():
                try:
                    record[field_name] = float(elem.text)
                except ValueError:
                    record[field_name] = np.nan
            else:
                record[field_name] = np.nan

        records.append(record)

    df = pd.DataFrame(records)
    if not df.empty:
        df = df.sort_values("date").reset_index(drop=True)
    return df
