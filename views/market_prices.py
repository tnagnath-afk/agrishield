import plotly.express as px
import streamlit as st

from config import data_gov_api_key
from utils.helpers import footer
from utils.live_prices import ATTRIBUTION, PriceAPIError, fetch_prices

st.title("💹 Market Prices")
st.caption("Latest wholesale mandi prices in Andhra Pradesh and Telangana, in ₹ per quintal (100 kg).")

key = data_gov_api_key()
if not key:
    st.warning(
        "Live prices need a free data.gov.in API key. Sign up at **data.gov.in** → My Account → "
        "generate API key, then add `DATA_GOV_IN_API_KEY = \"...\"` to the app's Secrets "
        "(Streamlit Cloud → App settings → Secrets, or `.streamlit/secrets.toml` locally)."
    )
    footer(ATTRIBUTION)
    st.stop()

try:
    prices = fetch_prices(key)
except PriceAPIError as exc:
    st.error(str(exc))
    footer(ATTRIBUTION)
    st.stop()
except Exception as exc:
    st.error(f"The price service could not be reached. Please try again later.\n\nDetails: {exc}")
    footer(ATTRIBUTION)
    st.stop()

if prices.empty:
    st.info("No price reports for AP or Telangana in today's feed yet. Markets usually report by afternoon.")
    footer(ATTRIBUTION)
    st.stop()

latest = prices["arrival_date"].max() if "arrival_date" in prices else None
c1, c2, c3 = st.columns(3)
c1.metric("Price reports", len(prices))
c2.metric("Markets", prices["market"].nunique())
c3.metric("Latest report", f"{latest:%d %b %Y}" if latest is not None and not str(latest) == "NaT" else "–")

f1, f2, f3 = st.columns(3)
commodities = sorted(prices["commodity"].unique())
default = commodities.index("Onion") if "Onion" in commodities else 0
commodity = f1.selectbox("Commodity", commodities, index=default)
states = ["All"] + sorted(prices["state"].unique())
state = f2.selectbox("State", states)
view = prices[prices["commodity"] == commodity]
if state != "All":
    view = view[view["state"] == state]
districts = ["All"] + sorted(view["district"].unique())
district = f3.selectbox("District", districts)
if district != "All":
    view = view[view["district"] == district]

if view.empty:
    st.info("No reports for this selection today.")
else:
    m1, m2, m3 = st.columns(3)
    m1.metric("Lowest modal price", f"₹{view['modal_price'].min():,.0f}")
    m2.metric("Average modal price", f"₹{view['modal_price'].mean():,.0f}")
    m3.metric("Highest modal price", f"₹{view['modal_price'].max():,.0f}")

    chart = view.sort_values("modal_price", ascending=False).head(25)
    fig = px.bar(chart, x="modal_price", y="market", color="state", orientation="h",
                 hover_data=["district", "variety", "min_price", "max_price"],
                 labels={"modal_price": "Modal price (₹/quintal)", "market": "Market"},
                 height=max(300, 26 * len(chart)))
    fig.update_layout(yaxis=dict(autorange="reversed"), margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig)

    cols = [c for c in ["state", "district", "market", "variety", "grade", "arrival_date",
                        "min_price", "max_price", "modal_price"] if c in view]
    st.dataframe(
        view[cols].sort_values("modal_price", ascending=False), hide_index=True,
        column_config={
            "arrival_date": st.column_config.DateColumn("Date", format="DD MMM YYYY"),
            "min_price": st.column_config.NumberColumn("Min ₹/q", format="%d"),
            "max_price": st.column_config.NumberColumn("Max ₹/q", format="%d"),
            "modal_price": st.column_config.NumberColumn("Modal ₹/q", format="%d"),
            "state": "State", "district": "District", "market": "Market", "variety": "Variety", "grade": "Grade",
        },
    )

footer(ATTRIBUTION + " Refreshed every 3 hours.")
