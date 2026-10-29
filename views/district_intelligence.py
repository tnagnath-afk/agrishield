import plotly.graph_objects as go
import streamlit as st

from utils.crop_engine import profiles_from_df
from utils.data_loader import RISK_COLUMNS, load_data, load_sheet
from utils.district_twin import build_twin
from utils.helpers import CATEGORY_ICON, district_picker, footer, live_rain, risk_badge
from utils.live_rainfall import ATTRIBUTION, adjust_water_risk
from utils.risk_engine import get_district_risk

st.title("🗺️ District Intelligence")

risk_df, food_df = load_data()
district = district_picker(risk_df, key="di_district")
risk = get_district_risk(district, risk_df)

if risk is None:
    st.warning("No data for this district.")
    st.stop()

st.markdown(
    f"**{district}, {risk['State']}** · {risk['Region']} · HQ {risk['HQ']} · "
    f"Recommended focus: **{risk['Recommended Focus']}**"
)
if risk.get("Score_Source") != "Original workbook":
    st.caption("Risk scores for this district are AgriShield estimates (Oct 2026).")

labels = {
    "ElNinoRisk": "El Niño", "WaterRisk": "Water", "FoodRisk": "Food",
    "FertilizerRisk": "Fertilizer", "FuelRisk": "Fuel", "PoultryFeedRisk": "Poultry feed",
}
cols = st.columns(4) + st.columns(4)
for col, key in zip(cols, RISK_COLUMNS):
    col.metric(f"{labels[key]} · {risk_badge(risk[key])}", f"{risk[key]}/10")
cols[len(RISK_COLUMNS)].metric("Business opportunity", f"{risk['OpportunityScore']}/10")

# ---------------------------------------------------------------- live rainfall
st.markdown("### 🌧️ Rainfall this season (live)")
rain, err = live_rain(risk_df, risk)
live_water = None
if rain is None:
    st.info(f"Live rainfall is unavailable right now, so the workbook scores are used. ({err})")
else:
    live_water = adjust_water_risk(risk["WaterRisk"], rain["departure_pct"])
    r1, r2, r3, r4 = st.columns(4)
    r1.metric(f"Since {rain['start']:%d %b}", f"{rain['season_mm']} mm")
    r2.metric("10-year average", f"{rain['normal_mm']} mm" if rain["normal_mm"] else "–")
    r3.metric(f"Departure · {CATEGORY_ICON.get(rain['category'], '')} {rain['category']}",
              f"{rain['departure_pct']:+d}%" if rain["departure_pct"] is not None else "–")
    r4.metric("Water risk, live-adjusted", f"{live_water}/10",
              help="Workbook water risk +1 if rainfall is deficient (−20% or worse), +2 if large deficient "
                   "(−60%), −1 if excess (+20%).")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=rain["dates"], y=rain["cum"], name=f"{rain['start'].year} season", mode="lines"))
    if rain["normal_curve"] is not None:
        n = rain["normal_curve"].iloc[: len(rain["dates"])]
        fig.add_trace(go.Scatter(x=rain["dates"][: len(n)], y=n.values, name="10-year average",
                                 mode="lines", line=dict(dash="dot")))
    fig.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10), yaxis_title="Cumulative rain (mm)",
                      legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig)
    st.caption(f"Data up to {rain['end']:%d %b %Y}. {ATTRIBUTION}")

# ---------------------------------------------------------------- profile
left, right = st.columns([3, 2])
with left:
    names = [labels[k] for k in RISK_COLUMNS]
    values = [risk[k] for k in RISK_COLUMNS]
    state_avg = risk_df[risk_df["State"] == risk["State"]][RISK_COLUMNS].mean()
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values + values[:1], theta=names + names[:1], fill="toself", name=district))
    fig.add_trace(go.Scatterpolar(
        r=list(state_avg.values) + [state_avg.values[0]], theta=names + names[:1],
        name=f"{risk['State']} average", line=dict(dash="dot"),
    ))
    fig.update_layout(polar=dict(radialaxis=dict(range=[0, 10])), height=440,
                      margin=dict(l=70, r=70, t=40, b=40), legend=dict(orientation="h", y=-0.08))
    st.plotly_chart(fig)

with right:
    profiles = profiles_from_df(load_sheet("Crop_Profiles"))
    twin = build_twin(district, risk, profiles, water_risk=live_water)
    st.markdown("#### Best-fit crops")
    for i, c in enumerate(twin["best_crops"][:5], start=1):
        st.write(f"{i}. **{c['crop']}** (score {c['score']})")

    st.markdown("#### Likely shortages")
    if twin["shortages"]:
        for item in twin["shortages"]:
            st.write(f"- {item}")
    else:
        st.write("No major shortages expected at current risk levels.")

    supplies = food_df[food_df["Consumer_District"] == district]
    st.markdown("#### Food supplied from")
    if supplies.empty:
        st.write("No supply routes recorded for this district yet.")
    else:
        for _, r in supplies.iterrows():
            st.write(f"- **{r['Commodity']}**: {r['Supplier_District_1']}, {r['Supplier_District_2']}, "
                     f"{r['Supplier_District_3']}")

    res = load_sheet("Reservoirs")
    if res is not None:
        serving = res[res["Districts_Served"].str.contains(district, case=False, na=False)]
        if not serving.empty:
            st.markdown("#### Reservoirs serving this district")
            for _, r in serving.iterrows():
                st.write(f"- **{r['Reservoir']}** ({r['Basin']}), {r['Gross_Capacity_TMC']} TMC capacity")

footer()
