import plotly.graph_objects as go
import streamlit as st

from utils.data_loader import load_data
from utils.food_network import get_food_sources
from utils.helpers import GEO_LAYOUT, footer

st.title("🚚 Food Network")
st.caption("Where each district gets its food from, and how risky the route is.")

risk_df, food_df = load_data()
coords = risk_df.set_index("District")[["Lat", "Lon"]]

c1, c2 = st.columns(2)
commodity = c1.selectbox("Commodity", sorted(food_df["Commodity"].unique()), key="fn_commodity")
consumers = sorted(food_df.loc[food_df["Commodity"] == commodity, "Consumer_District"].unique())
district = c2.selectbox("Consumer district", consumers, key="fn_district")

result = get_food_sources(commodity, district, food_df)

if result is None:
    st.warning("No supply route recorded for this combination.")
else:
    row = food_df[(food_df["Commodity"] == commodity) & (food_df["Consumer_District"] == district)].iloc[0]
    st.markdown(f"#### {commodity} → {district}")
    s1, s2, s3 = st.columns(3)
    s1.metric("Main supplier", result["source1"])
    s2.metric("Backup 1", result["source2"])
    s3.metric("Backup 2", result["source3"])
    m1, m2, m3 = st.columns(3)
    m1.metric("Transport", row["Transport_Mode"])
    m2.metric("Route risk", row["Risk_Level"])
    m3.metric("Season", row["Season"])

    fig = go.Figure()
    for label, src, width in [("Main", result["source1"], 4), ("Backup 1", result["source2"], 2),
                              ("Backup 2", result["source3"], 2)]:
        if src in coords.index and district in coords.index:
            fig.add_trace(go.Scattergeo(
                lat=[coords.loc[src, "Lat"], coords.loc[district, "Lat"]],
                lon=[coords.loc[src, "Lon"], coords.loc[district, "Lon"]],
                mode="lines+markers+text", line=dict(width=width), name=f"{label}: {src}",
                text=[src, ""], textposition="top right", marker=dict(size=9),
            ))
    if district in coords.index:
        fig.add_trace(go.Scattergeo(lat=[coords.loc[district, "Lat"]], lon=[coords.loc[district, "Lon"]],
                                    mode="markers+text", marker=dict(size=16, color="black"),
                                    text=[district], textposition="bottom right", name=f"Consumer: {district}"))
    fig.update_geos(**GEO_LAYOUT)
    fig.update_layout(height=480, margin=dict(l=0, r=0, t=0, b=0), legend=dict(orientation="h", y=0))
    st.plotly_chart(fig)

st.markdown("### All supply routes")
st.dataframe(food_df.rename(columns=lambda c: c.replace("_", " ")), hide_index=True)

footer()
