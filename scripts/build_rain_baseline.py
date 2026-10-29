"""Build data/rain_baseline.csv: 10-year mean cumulative rainfall per district.

Run once from the project folder (takes ~1 minute, 10 requests to Open-Meteo):

    python scripts/build_rain_baseline.py

Then commit data/rain_baseline.csv so the deployed app only needs one light
request per day for the current season. Rebuild once a year (e.g. each January).
"""

import datetime as dt
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import logging  # noqa: E402

import pandas as pd  # noqa: E402

logging.getLogger("streamlit").setLevel(logging.ERROR)  # hide 'No runtime found' notices

from config import WORKBOOK  # noqa: E402
from utils.live_rainfall import BASELINE_FILE, BASELINE_YEARS, build_baseline, season_window  # noqa: E402


def main():
    risk = pd.read_excel(WORKBOOK, sheet_name="Combined_Risk_Model").dropna(subset=["Lat", "Lon"])
    start, _ = season_window()
    end_year = start.year - 1  # last complete season
    print(f"Building {BASELINE_YEARS}-year baseline ({end_year - BASELINE_YEARS + 1}-{end_year}) "
          f"for {len(risk)} districts...")
    base = build_baseline(list(risk["District"]), list(risk["Lat"]), list(risk["Lon"]), end_year,
                          progress=lambda frac, msg: print(f"  {frac:4.0%}  {msg}"))
    base["MeanCumMM"] = base["MeanCumMM"].round(1)
    base.to_csv(BASELINE_FILE, index=False)
    print(f"Saved {BASELINE_FILE} ({len(base)} rows) at {dt.datetime.now():%Y-%m-%d %H:%M}")


if __name__ == "__main__":
    main()
