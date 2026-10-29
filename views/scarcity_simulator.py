import streamlit as st

from utils.data_loader import load_data
from utils.helpers import district_picker, footer
from utils.risk_engine import get_district_risk
from utils.scarcity_engine import predict_shortages

st.title("⚠️ Scarcity Simulator")
st.caption("Shows likely shortages for a district. Move the sliders to test a worse or better season.")

risk_df, _ = load_data()
district = district_picker(risk_df, key="ss_district")
risk = get_district_risk(district, risk_df)

if risk is None:
    st.warning("No data for this district.")
    st.stop()

st.markdown("#### Current outlook")
current = predict_shortages(risk)
if current:
    st.error("Likely shortages: " + ", ".join(current))
else:
    st.success("No major shortages expected at current risk levels.")

st.markdown("#### What-if scenario")
c1, c2 = st.columns(2)
water = c1.slider("Water risk", 1, 10, int(risk["WaterRisk"]), key=f"ss_water_{district}")
feed = c2.slider("Poultry feed risk", 1, 10, int(risk["PoultryFeedRisk"]), key=f"ss_feed_{district}")

scenario = dict(risk, WaterRisk=water, PoultryFeedRisk=feed)
simulated = predict_shortages(scenario)

if simulated:
    st.warning("In this scenario: " + ", ".join(simulated))
else:
    st.info("In this scenario, no major shortages are expected.")

st.caption("Rules: water risk 8+ → rice and fodder shortages; poultry feed risk 7+ → maize feed shortage.")

footer()
