# fred

Jupyter notebooks for analyzing economic data from FRED (Federal Reserve Economic Data) and the US Treasury.

## Contents

- [YieldCurve/YieldCurve.ipynb](YieldCurve/YieldCurve.ipynb) - Yield curve analysis using the FRED API
- [YieldCurve/DailyTreasuryParYieldCurve.ipynb](YieldCurve/DailyTreasuryParYieldCurve.ipynb) - Daily Treasury par yield curve from the Treasury XML feed

## Getting started

```bash
uv sync
cp .env.example .env  # then add your FRED API key
```

Get a free FRED API key at <https://research.stlouisfed.org/useraccount/apikey>.

Launch Jupyter with `uv run jupyter lab`.
