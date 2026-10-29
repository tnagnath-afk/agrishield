import pandas as pd
import streamlit as st

from config import WORKBOOK

RISK_COLUMNS = [
    "ElNinoRisk",
    "WaterRisk",
    "FoodRisk",
    "FertilizerRisk",
    "FuelRisk",
    "PoultryFeedRisk",
]


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    """Trim stray spaces so dropdown values match exactly."""
    for col in df.select_dtypes(include=["object", "string"]).columns:
        df[col] = df[col].where(df[col].isna(), df[col].astype(str).str.strip())
    return df


@st.cache_data(show_spinner=False)
def load_data():
    """Risk model and food network sheets, loaded once and cached."""
    risk_df = _clean(pd.read_excel(WORKBOOK, sheet_name="Combined_Risk_Model"))
    food_df = _clean(pd.read_excel(WORKBOOK, sheet_name="Food_Source_Network"))
    return risk_df, food_df


@st.cache_data(show_spinner=False)
def load_sheet(name: str):
    """Any other sheet (Crop_Profiles, Reservoirs, ...). Returns None if it doesn't exist."""
    try:
        return _clean(pd.read_excel(WORKBOOK, sheet_name=name))
    except ValueError:
        return None
