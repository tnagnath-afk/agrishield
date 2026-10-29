import streamlit as st

from utils.data_loader import load_data
from utils.helpers import CATEGORY_ICON, district_map, footer
from utils.live_rainfall import ATTRIBUTION, load_baseline_file, season_summary

st.title("🌧️ Rainfall Monitor")
st.caption("Season-to-date rainfall for every district, compared with the previous 10 years. Updates daily.")

risk_df, _ = load_data()

try:
    summary, start, end = season_summary(risk_df)
except Exception as exc:
    st.error(f"Live rainfall could not be loaded right now. Please try again later.\n\nDetails: {exc}")
    footer(ATTRIBUTION)
    st.stop()

has_baseline = load_baseline_file() is not None
st.markdown(f"**Season:** {start:%d %b %Y} – {end:%d %b %Y} (latest available data)")

if has_baseline:
    counts = summary["Category"].value_counts()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🔴 Large deficient (≤ −60%)", int(counts.get("Large deficient", 0)))
    c2.metric("🟠 Deficient (−20 to −59%)", int(counts.get("Deficient", 0)))
    c3.metric("🟢 Normal (±19%)", int(counts.get("Normal", 0)))
    c4.metric("🔵 Excess (+20% or more)", int(counts.get("Excess", 0) + counts.get("Large excess", 0)))
    color, scale, rng, title = "Departure_pct", "RdBu", (-80, 80), "% vs 10-yr avg"
else:
    st.info(
        "Departure from normal needs the 10-year baseline file `data/rain_baseline.csv`. "
        "Build it once with `python scripts/build_rain_baseline.py` and push it to GitHub. "
        "Until then, season totals are shown."
    )
    color, scale, rng, title = "Season_mm", "Blues", None, "mm"

state = st.radio("State", ["All", "AP", "TG"], horizontal=True,
                 format_func=lambda s: {"All": "AP + TG", "AP": "Andhra Pradesh", "TG": "Telangana"}[s])
view = summary if state == "All" else summary[summary["State"] == state]

fig = district_map(
    view, color=color, scale=scale, range_color=rng, colorbar=title,
    hover_data={"Season_mm": True, "Normal_mm": has_baseline, "Departure_pct": has_baseline,
                "Category": has_baseline},
)
st.plotly_chart(fig)

table = view.sort_values("Departure_pct" if has_baseline else "Season_mm").copy()
table["Category"] = table["Category"].map(lambda c: f"{CATEGORY_ICON.get(c, '')} {c}")
cols = ["District", "State", "Region", "Season_mm"] + (["Normal_mm", "Departure_pct", "Category"] if has_baseline else [])
st.dataframe(table[cols].rename(columns={"Season_mm": "Season (mm)", "Normal_mm": "10-yr avg (mm)",
                                         "Departure_pct": "Departure (%)"}), hide_index=True)

footer(ATTRIBUTION + " Categories follow IMD thresholds.")
