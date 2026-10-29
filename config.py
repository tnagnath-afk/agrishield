"""Central settings: file paths and secrets.

Secrets are read from Streamlit secrets (Streamlit Cloud → App settings → Secrets,
or .streamlit/secrets.toml locally). Environment variables are used as a fallback.
Never commit real keys to git.
"""

import os
from pathlib import Path

import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
WORKBOOK = BASE_DIR / "data" / "AP_TG_ElNino_War_Risk_Workbook.xlsx"

DEFAULT_GEMINI_MODEL = "gemini-3.8-flash"


def get_secret(*names: str, default: str = "") -> str:
    """Return the first secret found under any of `names`.

    Works even when no secrets.toml exists (st.secrets raises in that case).
    """
    for name in names:
        try:
            value = st.secrets.get(name)
        except Exception:  # no secrets file configured
            value = None
        if not value:
            value = os.environ.get(name)
        if value and not str(value).strip().lower().startswith("paste-your"):  # ignore template placeholders
            return str(value).strip()
    return default


def gemini_api_key() -> str:
    # Accept both names: the old .env used GEMINI_API_KEY, config used GOOGLE_API_KEY.
    return get_secret("GEMINI_API_KEY", "GOOGLE_API_KEY")


def gemini_model() -> str:
    return get_secret("GEMINI_MODEL", default=DEFAULT_GEMINI_MODEL)


def data_gov_api_key() -> str:
    """Free key from data.gov.in (My Account → API key) for live mandi prices."""
    return get_secret("DATA_GOV_IN_API_KEY")
