def get_district_risk(
    district,
    risk_df
):

    data = risk_df[
        risk_df["District"] == district
    ]

    if data.empty:
        return None

    return data.iloc[0].to_dict()