"""AgriShield entry point. Streamlit Cloud "Main file path": app.py"""

import streamlit as st

from config import data_gov_api_key

st.set_page_config(page_title="AgriShield", page_icon="🌾", layout="wide")

pages = {
    "Overview": [
        st.Page("views/home.py", title="Home", icon="🌾", default=True),
        st.Page("views/district_intelligence.py", title="District Intelligence", icon="🗺️", url_path="district"),
    ],
    "Live data": [
        st.Page("views/rainfall_monitor.py", title="Rainfall Monitor", icon="🌧️", url_path="rainfall"),
        st.Page("views/reservoirs.py", title="Reservoirs", icon="💧", url_path="reservoirs"),
    ],
    "Planning tools": [
        st.Page("views/crop_advisor.py", title="Crop Advisor", icon="🌱", url_path="crops"),
        st.Page("views/food_network.py", title="Food Network", icon="🚚", url_path="food"),
        st.Page("views/scarcity_simulator.py", title="Scarcity Simulator", icon="⚠️", url_path="scarcity"),
        st.Page("views/ai_advisor.py", title="AI Advisor", icon="🤖", url_path="ai"),
    ],
}

# Market Prices appears in the menu only once a data.gov.in key is configured.
if data_gov_api_key():
    pages["Live data"].insert(1, st.Page("views/market_prices.py", title="Market Prices", icon="💹",
                                         url_path="prices"))

st.navigation(pages).run()
