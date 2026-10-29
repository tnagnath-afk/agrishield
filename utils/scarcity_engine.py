def predict_shortages(
    risk_data
):

    shortages = []

    if risk_data["WaterRisk"] >= 8:
        shortages.append(
            "Rice"
        )

        shortages.append(
            "Fodder"
        )

    if risk_data["PoultryFeedRisk"] >= 7:
        shortages.append(
            "Maize Feed"
        )

    return shortages