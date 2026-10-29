"""Crop suitability scoring. Profiles come from the workbook sheet Crop_Profiles;
the dictionary below is the fallback (the original four crops)."""

crop_profiles = {
    "Paddy": {"water": 10, "drought": 2},
    "Groundnut": {"water": 5, "drought": 8},
    "Red Gram": {"water": 4, "drought": 9},
    "Millets": {"water": 3, "drought": 10},
}


def profiles_from_df(df):
    """Build {crop: {water, drought, season, duration, areas}} from the Crop_Profiles sheet."""
    if df is None or df.empty:
        return crop_profiles
    out = {}
    for _, r in df.iterrows():
        out[str(r["Crop"])] = {
            "water": float(r["Water"]),
            "drought": float(r["Drought"]),
            "season": str(r.get("Season", "")),
            "duration": r.get("Duration_Days"),
            "areas": str(r.get("Typical_Areas", "")),
        }
    return out


def crop_score(crop, water_risk, profiles=None):
    profile = (profiles or crop_profiles)[crop]
    score = profile["drought"] * 0.6 + (10 - profile["water"]) * 0.4
    if water_risk >= 8:
        score += profile["drought"]
    return round(score, 2)


def rank_crops(district, risk_data, profiles=None, water_risk=None, season=None):
    """Rank crops for a district. `water_risk` overrides the workbook score (e.g. live-adjusted).
    `season` ('Kharif' / 'Rabi') keeps only crops grown in that season."""
    profiles = profiles or crop_profiles
    wr = risk_data["WaterRisk"] if water_risk is None else water_risk
    results = []
    for crop, p in profiles.items():
        if season and p.get("season") and season not in p["season"] and "All" not in p["season"]:
            continue
        results.append({"crop": crop, "score": crop_score(crop, wr, profiles)})
    return sorted(results, key=lambda x: x["score"], reverse=True)
