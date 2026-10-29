import streamlit as st

from utils.data_loader import RISK_COLUMNS, load_data
from utils.helpers import district_map, footer, risk_badge

st.title("🌾 AgriShield")
st.subheader("Food security & crop intelligence for Andhra Pradesh and Telangana")

st.markdown(
    "AgriShield shows how the **2026–27 El Niño** and global supply shocks "
    "(fuel, fertilizer, feed) could affect each district: which crops fit the risk, "
    "where food comes from, what might run short, plus **live rainfall** and **mandi prices**."
)

risk_df, food_df = load_data()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Districts covered", len(risk_df), help="Andhra Pradesh 28 + Telangana 33")
c2.metric("High El Niño risk", int((risk_df["ElNinoRisk"] >= 8).sum()))
c3.metric("High water risk", int((risk_df["WaterRisk"] >= 8).sum()))
c4.metric("Food supply routes", len(food_df))

st.markdown("### El Niño risk map")
measure = st.radio(
    "Colour districts by", ["ElNinoRisk", "WaterRisk", "FoodRisk", "OpportunityScore"], horizontal=True,
    format_func=lambda c: {"ElNinoRisk": "El Niño risk", "WaterRisk": "Water risk",
                           "FoodRisk": "Food risk", "OpportunityScore": "Business opportunity"}[c],
)
fig = district_map(
    risk_df, color=measure, hover_data={"State": True, "Region": True, measure: True},
    scale="RdYlGn_r" if measure != "OpportunityScore" else "Greens", range_color=(1, 10), colorbar="1–10",
)
st.plotly_chart(fig)

st.markdown("### All districts")
overview = risk_df.sort_values(["ElNinoRisk", "WaterRisk"], ascending=False)
table = overview[["District", "State", "Region", *RISK_COLUMNS, "OpportunityScore", "Recommended Focus",
                  "Score_Source"]].copy()
table.insert(2, "El Niño level", table["ElNinoRisk"].map(risk_badge))
table = table.rename(columns=lambda c: c.replace("Risk", " risk").replace("OpportunityScore", "Opportunity")
                     .replace("ElNino", "El Niño").replace("PoultryFeed", "Poultry feed")
                     .replace("Score_Source", "Score source"))
st.dataframe(table, hide_index=True)

st.info("Open a page from the menu on the left (tap ☰ / » on a phone).", icon="👈")

footer()
