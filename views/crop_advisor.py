import pandas as pd
import plotly.express as px
import streamlit as st

from utils.crop_engine import profiles_from_df, rank_crops
from utils.data_loader import load_data, load_sheet
from utils.helpers import district_picker, footer, live_rain, risk_badge
from utils.live_rainfall import adjust_water_risk
from utils.risk_engine import get_district_risk

st.title("🌱 Crop Advisor")
st.caption("Ranks crops by drought tolerance and water need, weighted by the district's water risk.")

risk_df, _ = load_data()
district = district_picker(risk_df, key="ca_district")
risk = get_district_risk(district, risk_df)

if risk is None:
    st.warning("No data for this district.")
    st.stop()

profiles = profiles_from_df(load_sheet("Crop_Profiles"))

c1, c2 = st.columns(2)
season = c1.radio("Season", ["Any", "Kharif", "Rabi"], index=2, horizontal=True,
                  help="Kharif = June–October (monsoon). Rabi = October–March.")
use_live = c2.toggle("Adjust for live rainfall", value=True,
                     help="Raises water risk when this season's rain is deficient, lowers it when in excess.")

water = risk["WaterRisk"]
if use_live:
    rain, err = live_rain(risk_df, risk)
    if rain is None:
        st.info("Live rainfall unavailable right now; using the workbook water risk.")
    else:
        water = adjust_water_risk(risk["WaterRisk"], rain["departure_pct"])
        dep = f"{rain['departure_pct']:+d}%" if rain["departure_pct"] is not None else "n/a"
        st.caption(f"Season rainfall {rain['season_mm']} mm ({dep} vs 10-year average, {rain['category']}).")

st.markdown(f"Water risk used for **{district}**: **{water}/10** ({risk_badge(water)})"
            + (f", workbook value {risk['WaterRisk']}/10" if water != risk["WaterRisk"] else ""))

ranking = pd.DataFrame(rank_crops(district, risk, profiles, water_risk=water,
                                  season=None if season == "Any" else season))
if ranking.empty:
    st.warning("No crops match this season filter.")
    st.stop()

ranking["Water need (1–10)"] = ranking["crop"].map(lambda c: profiles[c]["water"])
ranking["Drought tolerance (1–10)"] = ranking["crop"].map(lambda c: profiles[c]["drought"])
ranking["Season"] = ranking["crop"].map(lambda c: profiles[c].get("season", ""))
ranking["Days"] = ranking["crop"].map(lambda c: profiles[c].get("duration", ""))
ranking["Typical areas"] = ranking["crop"].map(lambda c: profiles[c].get("areas", ""))
ranking = ranking.rename(columns={"crop": "Crop", "score": "Suitability score"})

st.success(f"Best fit for {district} right now: **{ranking.iloc[0]['Crop']}**, then "
           f"{', '.join(ranking['Crop'].iloc[1:3])}")

fig = px.bar(ranking, x="Suitability score", y="Crop", orientation="h", text="Suitability score",
             height=max(280, 30 * len(ranking)))
fig.update_layout(yaxis=dict(autorange="reversed"), margin=dict(l=10, r=10, t=10, b=10))
st.plotly_chart(fig)

st.dataframe(ranking, hide_index=True)

if water >= 8:
    st.info(
        "Water risk is high, so drought tolerance gets extra weight. Prefer short-duration, low-water "
        "crops (pulses, millets) and avoid paddy or sugarcane unless there is assured canal water."
    )

footer()
