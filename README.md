# 🌾 AgriShield

Food security and crop intelligence for all 61 districts of Andhra Pradesh (28) and Telangana (33)
during the 2026–27 El Niño, with live rainfall and mandi prices.

| Page | What it does | Data |
| --- | --- | --- |
| Home | Risk map and table for all districts | Workbook |
| District Intelligence | Risk profile, live season rainfall, best crops, shortages, supply routes, reservoirs | Workbook + live rainfall |
| Rainfall Monitor | Season-to-date rainfall and departure from the 10-year average, every district | Live (Open-Meteo) |
| Market Prices | Today's wholesale mandi prices in AP and TG | Live (data.gov.in) |
| Reservoirs | Major reservoirs, capacity, districts served, latest reported storage | Workbook (update weekly) |
| Crop Advisor | 18 crops ranked for the district's water risk, by season, adjusted for live rainfall | Workbook + live rainfall |
| Food Network | 52 supply routes with a route map | Workbook |
| Scarcity Simulator | Likely shortages and what-if sliders | Workbook |
| AI Advisor | Gemini answers using the district's data and live rainfall | Gemini API |

Every live feed has a fallback: if a source is down, the page says so and keeps working with workbook data.

## Data

`data/AP_TG_ElNino_War_Risk_Workbook.xlsx` – sheets `Combined_Risk_Model`, `Food_Source_Network`,
`Crop_Profiles`, `Reservoirs` (+ original impact sheets). The 10 original districts keep their original
scores; the other 51 are AgriShield estimates (column `Score_Source`). Edit the workbook and push to update the app.

Live sources:
- **Rainfall** – ERA5 reanalysis via [Open-Meteo](https://open-meteo.com) (free, no key, non-commercial use, CC BY 4.0). ~5-day delay. Estimates, not IMD gauge data.
- **Mandi prices** – Agmarknet via [data.gov.in](https://data.gov.in) (free API key).

`data/rain_baseline.csv` holds the 10-year average used for "departure from normal". Build it once:

```bash
python scripts/build_rain_baseline.py
```

then commit the CSV. Rebuild once a year.

## Secrets

Local: copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and fill in.
Streamlit Cloud: App settings → Secrets.

```toml
GEMINI_API_KEY = "..."        # AI Advisor
DATA_GOV_IN_API_KEY = "..."   # Market Prices (data.gov.in → My Account → API key)
```

Never commit `secrets.toml` or `.env` (both are in `.gitignore`).

## Run locally (Windows)

```cmd
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud

1. Push this folder to GitHub.
2. https://share.streamlit.io → **Create app** → repo, branch `main`, main file `app.py`.
3. Advanced settings → Python 3.11 or 3.12 → Secrets → paste the keys.
4. **Deploy**. Later updates: `git add . && git commit -m "..." && git push` – the app redeploys automatically.

## Project layout

```
app.py                  entry point (navigation)
views/                  one file per page
utils/                  data loading, scoring, live feeds, Gemini helper
scripts/                build_rain_baseline.py
data/                   workbook (+ rain_baseline.csv once built)
config.py               paths + secrets
.streamlit/config.toml  theme
```
