import pandas as pd
import streamlit as st

from utils.data_loader import load_sheet
from utils.helpers import footer

st.title("💧 Reservoirs")
st.caption("Major reservoirs feeding Andhra Pradesh and Telangana, and the districts that depend on them.")

res = load_sheet("Reservoirs")
if res is None:
    st.warning("The workbook has no Reservoirs sheet.")
    st.stop()

res = res.copy()
res["Current_Storage_TMC"] = pd.to_numeric(res["Current_Storage_TMC"], errors="coerce")
res["Pct_Of_Normal"] = pd.to_numeric(res["Pct_Of_Normal"], errors="coerce")
res["Pct_Full"] = (res["Current_Storage_TMC"] / res["Gross_Capacity_TMC"] * 100).round(0)

reported = res[res["Current_Storage_TMC"].notna() | res["Pct_Of_Normal"].notna()]
if not reported.empty:
    st.markdown("#### Latest reported levels")
    for _, r in reported.iterrows():
        parts = []
        if pd.notna(r["Current_Storage_TMC"]):
            parts.append(f"{r['Current_Storage_TMC']:.1f} of {r['Gross_Capacity_TMC']:.1f} TMC ({r['Pct_Full']:.0f}% full)")
        if pd.notna(r["Pct_Of_Normal"]):
            parts.append(f"{r['Pct_Of_Normal']:.0f}% of normal storage for this time of year")
        st.write(f"- **{r['Reservoir']}**: {'; '.join(parts)} · as of {r['As_Of']} · {r['Source']}")

district = st.text_input("Find reservoirs serving a district", placeholder="e.g. Kurnool")
view = res
if district.strip():
    view = res[res["Districts_Served"].str.contains(district.strip(), case=False, na=False)]

st.dataframe(
    view[["Reservoir", "Basin", "State", "Located_In", "Gross_Capacity_TMC", "Current_Storage_TMC",
          "Pct_Full", "Pct_Of_Normal", "As_Of", "Districts_Served"]].rename(columns={
        "Located_In": "Located in", "Gross_Capacity_TMC": "Capacity (TMC)",
        "Current_Storage_TMC": "Storage (TMC)", "Pct_Full": "% full", "Pct_Of_Normal": "% of normal",
        "As_Of": "As of", "Districts_Served": "Districts served"}),
    hide_index=True,
)

st.info(
    "There is no free live feed for these reservoirs. To update: open the latest **Central Water "
    "Commission weekly bulletin** (cwc.gov.in → Reservoir level & storage bulletin), enter the storage in "
    "the workbook's *Reservoirs* sheet (Current_Storage_TMC, As_Of, Source), and push to GitHub.",
    icon="ℹ️",
)

footer("Capacities are approximate gross storage in TMC ft (1 TMC ≈ 28.3 million m³).")
