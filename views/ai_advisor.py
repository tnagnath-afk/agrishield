import datetime as dt

import streamlit as st

from config import gemini_api_key, gemini_model
from utils.ai_advisor import ask_ai, setup_ai
from utils.data_loader import load_data, load_sheet
from utils.helpers import district_picker, footer, live_rain
from utils.risk_engine import get_district_risk

st.title("🤖 AI Advisor")
st.caption("Ask about crops, water, food supply or drought planning. Answers come from Google Gemini.")

client = setup_ai(gemini_api_key())
if client is None:
    st.warning(
        "The AI Advisor is not set up yet. Add `GEMINI_API_KEY` in Streamlit Cloud under "
        "**App settings → Secrets** (or in `.streamlit/secrets.toml` when running locally)."
    )
    footer()
    st.stop()

risk_df, food_df = load_data()
district = district_picker(risk_df, key="ai_district", label="District for context")
risk = get_district_risk(district, risk_df) or {}
routes = food_df[food_df["Consumer_District"] == district]
crops = load_sheet("Crop_Profiles")

rain_line = "Live rainfall: unavailable."
if risk:
    rain, _ = live_rain(risk_df, risk)
    if rain is not None:
        rain_line = (f"Live rainfall since {rain['start']:%d %b %Y} up to {rain['end']:%d %b %Y}: "
                     f"{rain['season_mm']} mm vs 10-year average {rain['normal_mm']} mm "
                     f"(departure {rain['departure_pct']}%, IMD category {rain['category']}; ERA5 estimate).")

context = (
    f"Today is {dt.date.today():%d %B %Y}. AgriShield platform for Andhra Pradesh and Telangana. "
    "Risk scores are 1–10 (10 = highest risk).\n"
    f"District data: {risk}\n{rain_line}\n"
    f"Food supply routes into {district}: {routes.to_dict('records')}\n"
    f"Crop profiles (water need, drought tolerance 1–10): "
    f"{crops[['Crop', 'Water', 'Drought', 'Season']].to_dict('records') if crops is not None else 'n/a'}"
)
st.caption(rain_line)

with st.form("ask"):
    question = st.text_area(
        "Your question",
        placeholder=f"e.g. Which crops should farmers in {district} plant this rabi season?",
        height=120,
    )
    submitted = st.form_submit_button("Ask")

if submitted:
    if not question.strip():
        st.warning("Please type a question first.")
    else:
        with st.spinner("Thinking..."):
            try:
                answer = ask_ai(client, gemini_model(), context, question.strip())
            except Exception as exc:  # network, quota, invalid key, unknown model
                st.error(f"The AI service returned an error. Please try again later.\n\nDetails: {exc}")
            else:
                st.markdown(answer)

footer()
