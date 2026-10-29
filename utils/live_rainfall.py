"""Live season rainfall per district from Open-Meteo (ERA5 reanalysis, free, no key).

Season = 1 June of the current monsoon year up to ~6 days ago (ERA5 has a ~5-day delay).
Departure is compared with the mean of the previous 10 years for the same window,
read from data/rain_baseline.csv (built once with scripts/build_rain_baseline.py).
If that file is missing, the baseline for a single district is fetched on demand.

ERA5 is a satellite/model reanalysis, not IMD rain-gauge data: treat values as estimates.
Open-Meteo free tier is for non-commercial use (CC BY 4.0, attribution shown in the app).
"""

from __future__ import annotations

import datetime as dt

import pandas as pd
import requests
import streamlit as st

from config import BASE_DIR

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
BASELINE_FILE = BASE_DIR / "data" / "rain_baseline.csv"
BASELINE_YEARS = 10
DATA_DELAY_DAYS = 6
ATTRIBUTION = "Rainfall: ERA5 reanalysis via Open-Meteo.com (CC BY 4.0). Estimates, not IMD gauge data."


# ------------------------------------------------------------------ helpers
def season_window(today: dt.date | None = None) -> tuple[dt.date, dt.date]:
    """1 June of the monsoon year → latest day with ERA5 data."""
    today = today or dt.date.today()
    end = today - dt.timedelta(days=DATA_DELAY_DAYS)
    year = end.year if end >= dt.date(end.year, 6, 1) else end.year - 1
    return dt.date(year, 6, 1), end


def imd_category(departure_pct: float | None) -> str:
    """IMD rainfall categories by % departure from normal."""
    if departure_pct is None or pd.isna(departure_pct):
        return "No data"
    if departure_pct <= -99.5:
        return "No rain"
    if departure_pct <= -60:
        return "Large deficient"
    if departure_pct <= -20:
        return "Deficient"
    if departure_pct < 20:
        return "Normal"
    if departure_pct < 60:
        return "Excess"
    return "Large excess"


def _get(params: dict) -> list[dict]:
    resp = requests.get(ARCHIVE_URL, params=params, timeout=40)
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, dict) and data.get("error"):
        raise RuntimeError(data.get("reason", "Open-Meteo error"))
    return data if isinstance(data, list) else [data]


def _fetch_daily(lats, lons, start: dt.date, end: dt.date) -> list[pd.Series]:
    """One request for many points; returns a daily precipitation Series per point."""
    payload = _get({
        "latitude": ",".join(f"{x:.3f}" for x in lats),
        "longitude": ",".join(f"{x:.3f}" for x in lons),
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "daily": "precipitation_sum",
        "timezone": "Asia/Kolkata",
    })
    out = []
    for loc in payload:
        daily = loc.get("daily", {})
        s = pd.Series(daily.get("precipitation_sum", []), index=pd.to_datetime(daily.get("time", [])), dtype="float")
        out.append(s)
    return out


# ------------------------------------------------------------------ season (all districts, one call)
@st.cache_data(ttl=12 * 3600, show_spinner="Fetching live rainfall...")
def fetch_season_all(districts: tuple, lats: tuple, lons: tuple, start: str, end: str) -> pd.DataFrame:
    """Daily rainfall this season for every district. Columns = districts, index = date."""
    series = _fetch_daily(lats, lons, dt.date.fromisoformat(start), dt.date.fromisoformat(end))
    return pd.DataFrame({d: s for d, s in zip(districts, series)})


# ------------------------------------------------------------------ baseline
def build_baseline(districts, lats, lons, end_year: int, years: int = BASELINE_YEARS, progress=None) -> pd.DataFrame:
    """Mean cumulative rainfall by day since 1 June over `years` seasons ending `end_year`.

    One multi-location request per year (Jun 1 – Dec 31). Returns long table:
    District, Day (0 = 1 June), MeanCumMM.
    """
    per_year = []
    for i, year in enumerate(range(end_year - years + 1, end_year + 1)):
        series = _fetch_daily(lats, lons, dt.date(year, 6, 1), dt.date(year, 12, 31))
        cum = pd.DataFrame({d: s.fillna(0).cumsum().reset_index(drop=True) for d, s in zip(districts, series)})
        per_year.append(cum)
        if progress:
            progress((i + 1) / years, f"Season {year} done")
    mean = sum(per_year) / len(per_year)
    long = mean.reset_index(names="Day").melt(id_vars="Day", var_name="District", value_name="MeanCumMM")
    return long[["District", "Day", "MeanCumMM"]]


@st.cache_data(show_spinner=False)
def load_baseline_file() -> pd.DataFrame | None:
    if BASELINE_FILE.exists():
        return pd.read_csv(BASELINE_FILE)
    return None


@st.cache_data(ttl=30 * 24 * 3600, show_spinner="Building 10-year rainfall baseline for this district...")
def baseline_for_one(district: str, lat: float, lon: float, end_year: int) -> pd.DataFrame:
    return build_baseline([district], [lat], [lon], end_year)


def normal_to_date(district: str, lat: float, lon: float, start: dt.date, end: dt.date) -> pd.Series | None:
    """Mean cumulative rainfall curve (index = day since 1 June) for a district."""
    base = load_baseline_file()
    if base is None or district not in set(base["District"]):
        base = baseline_for_one(district, lat, lon, start.year - 1)
    curve = base[base["District"] == district].set_index("Day")["MeanCumMM"].sort_index()
    return curve if not curve.empty else None


# ------------------------------------------------------------------ public API used by pages
def season_summary(risk_df: pd.DataFrame, with_departure: bool = True) -> tuple[pd.DataFrame, dt.date, dt.date]:
    """Season-to-date rainfall for all districts (+ departure where a baseline exists)."""
    start, end = season_window()
    df = risk_df.dropna(subset=["Lat", "Lon"])
    totals = season_daily_all(risk_df).fillna(0).sum()
    out = df[["District", "State", "Region", "Lat", "Lon"]].copy()
    out["Season_mm"] = out["District"].map(totals).round(0)

    base = load_baseline_file() if with_departure else None
    if base is not None:
        day = (end - start).days
        normal = base[base["Day"] == min(day, base["Day"].max())].set_index("District")["MeanCumMM"]
        out["Normal_mm"] = out["District"].map(normal).round(0)
        out["Departure_pct"] = ((out["Season_mm"] - out["Normal_mm"]) / out["Normal_mm"] * 100).round(0)
    else:
        out["Normal_mm"] = pd.NA
        out["Departure_pct"] = pd.NA
    out["Category"] = out["Departure_pct"].map(lambda v: imd_category(None if pd.isna(v) else float(v)))
    return out, start, end


def season_daily_all(risk_df: pd.DataFrame) -> pd.DataFrame:
    """Shared, cached call for every district (one API request serves all pages)."""
    start, end = season_window()
    df = risk_df.dropna(subset=["Lat", "Lon"])
    return fetch_season_all(tuple(df["District"]), tuple(df["Lat"]), tuple(df["Lon"]),
                            start.isoformat(), end.isoformat())


def district_detail(risk_df: pd.DataFrame, risk_row: dict) -> dict:
    """Season rainfall, normal and cumulative curves for one district."""
    start, end = season_window()
    daily = season_daily_all(risk_df)[risk_row["District"]].fillna(0)
    cum = daily.cumsum().reset_index(drop=True)
    normal_curve = normal_to_date(risk_row["District"], float(risk_row["Lat"]), float(risk_row["Lon"]), start, end)
    day = (end - start).days
    season = float(cum.iloc[-1]) if len(cum) else 0.0
    normal = float(normal_curve.loc[min(day, normal_curve.index.max())]) if normal_curve is not None else None
    dep = round((season - normal) / normal * 100) if normal else None
    return {
        "start": start, "end": end, "season_mm": round(season), "normal_mm": round(normal) if normal else None,
        "departure_pct": dep, "category": imd_category(dep), "cum": cum, "normal_curve": normal_curve,
        "dates": pd.date_range(start, periods=len(cum)),
    }


def adjust_water_risk(base_score: float, departure_pct: float | None) -> int:
    """Nudge the workbook water risk with live rainfall: deficits raise it, excess lowers it."""
    if departure_pct is None or pd.isna(departure_pct):
        return int(base_score)
    step = 2 if departure_pct <= -60 else 1 if departure_pct <= -20 else -1 if departure_pct >= 20 else 0
    return int(max(1, min(10, base_score + step)))
