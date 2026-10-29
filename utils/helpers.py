import streamlit as st

DISCLAIMER = (
    "Risk scores are indicative 1–10 estimates from the AgriShield workbook (10 districts from the "
    "original model, the rest AgriShield estimates), not official government data. Check local "
    "advisories before making farming or business decisions."
)


def risk_level(score) -> str:
    try:
        score = float(score)
    except (TypeError, ValueError):
        return "Unknown"
    if score >= 8:
        return "High"
    if score >= 6:
        return "Medium"
    return "Low"


def risk_badge(score) -> str:
    level = risk_level(score)
    icon = {"High": "🔴", "Medium": "🟠", "Low": "🟢"}.get(level, "⚪")
    return f"{icon} {level}"


CATEGORY_ICON = {
    "Large deficient": "🔴", "Deficient": "🟠", "Normal": "🟢",
    "Excess": "🔵", "Large excess": "🔵", "No rain": "⚫", "No data": "⚪",
}


def district_picker(risk_df, key: str, label: str = "District", state_filter: bool = True):
    """Shared district dropdown (optionally filtered by state); remembers the choice across pages."""
    df = risk_df
    if state_filter:
        states = ["All", "AP", "TG"]
        saved_state = st.session_state.get("state_choice", "All")
        c1, c2 = st.columns([1, 3])
        state = c1.selectbox("State", states, index=states.index(saved_state), key=f"{key}_state",
                             format_func=lambda s: {"All": "AP + TG", "AP": "Andhra Pradesh", "TG": "Telangana"}[s])
        st.session_state["state_choice"] = state
        if state != "All":
            df = risk_df[risk_df["State"] == state]
        container = c2
    else:
        container = st
    districts = sorted(df["District"].unique())
    default = st.session_state.get("district", "Kurnool")
    index = districts.index(default) if default in districts else 0
    choice = container.selectbox(label, districts, index=index, key=key)
    st.session_state["district"] = choice
    return choice


def live_rain(risk_df, risk_row):
    """District rainfall detail, or (None, error message) when the live source is unreachable."""
    from utils.live_rainfall import district_detail  # local import keeps pages fast when unused

    try:
        return district_detail(risk_df, risk_row), None
    except Exception as exc:  # network, rate limit, API change
        return None, str(exc)


# Map framing for AP + Telangana. Uses plotly "geo" (SVG), which works without WebGL or map tiles.
GEO_LAYOUT = dict(
    lataxis_range=[12.4, 20.2], lonaxis_range=[76.4, 85.2], projection_type="mercator",
    showcountries=True, countrycolor="#9aa59a", showcoastlines=True, coastlinecolor="#9aa59a",
    showland=True, landcolor="#f4f6f1", showocean=True, oceancolor="#dfeaf2", showlakes=False,
    resolution=50, bgcolor="rgba(0,0,0,0)",
)


def district_map(df, color, hover_data=None, scale="RdYlGn_r", range_color=None, colorbar="", height=560):
    """Dot map of district HQs coloured by a column."""
    import plotly.express as px

    hover = {"Lat": False, "Lon": False, **(hover_data or {})}
    fig = px.scatter_geo(df, lat="Lat", lon="Lon", color=color, hover_name="District", hover_data=hover,
                         color_continuous_scale=scale, range_color=range_color, height=height)
    fig.update_traces(marker=dict(size=14, line=dict(width=0.6, color="white")))
    fig.update_geos(**GEO_LAYOUT)
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), coloraxis_colorbar_title=colorbar)
    return fig


def footer(extra: str | None = None):
    st.divider()
    if extra:
        st.caption(extra)
    st.caption(DISCLAIMER)
