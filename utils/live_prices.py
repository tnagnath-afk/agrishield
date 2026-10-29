"""Live mandi prices from data.gov.in (Agmarknet "Current Daily Price of Various
Commodities from Various Markets"). Needs a free API key from data.gov.in
(Sign up → My Account → API key) stored as secret DATA_GOV_IN_API_KEY.

Prices are in ₹ per quintal (100 kg). The feed only holds the latest reported day per market.
"""

from __future__ import annotations

import pandas as pd
import requests
import streamlit as st

API_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
STATES = ("Andhra Pradesh", "Telangana")
PAGE_SIZE = 1000
MAX_PAGES = 10
ATTRIBUTION = "Prices: Agmarknet via data.gov.in (Open Government Data License – India)."


class PriceAPIError(RuntimeError):
    pass


def _page(api_key: str, state: str, offset: int, filter_field: str) -> dict:
    resp = requests.get(API_URL, params={
        "api-key": api_key, "format": "json", "limit": PAGE_SIZE, "offset": offset,
        f"filters[{filter_field}]": state,
    }, timeout=40)
    if resp.status_code in (401, 403):
        raise PriceAPIError("data.gov.in rejected the API key (check DATA_GOV_IN_API_KEY).")
    resp.raise_for_status()
    data = resp.json()
    if str(data.get("status", "ok")).lower() == "error":
        raise PriceAPIError(data.get("message", "data.gov.in returned an error."))
    return data


def _fetch_state(api_key: str, state: str) -> list[dict]:
    # The API has used both filter spellings over time; try the current one first.
    for field in ("state.keyword", "state"):
        records, offset = [], 0
        for _ in range(MAX_PAGES):
            data = _page(api_key, state, offset, field)
            batch = data.get("records", []) or []
            records.extend(batch)
            if len(batch) < PAGE_SIZE:
                break
            offset += PAGE_SIZE
        if records:
            return records
    return []


@st.cache_data(ttl=3 * 3600, show_spinner="Fetching today's mandi prices...")
def fetch_prices(api_key: str) -> pd.DataFrame:
    if not api_key:
        raise PriceAPIError("No DATA_GOV_IN_API_KEY configured.")
    rows = []
    for state in STATES:
        rows.extend(_fetch_state(api_key, state))
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df.columns = [c.strip().lower() for c in df.columns]
    for col in ("min_price", "max_price", "modal_price"):
        if col in df:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "arrival_date" in df:
        df["arrival_date"] = pd.to_datetime(df["arrival_date"], format="%d/%m/%Y", errors="coerce")
    for col in ("state", "district", "market", "commodity", "variety"):
        if col in df:
            df[col] = df[col].astype(str).str.strip()
    return df
