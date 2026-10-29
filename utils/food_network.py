def get_food_sources(
    commodity,
    district,
    food_df
):

    result = food_df[
        (food_df["Commodity"] == commodity)
        &
        (
            food_df["Consumer_District"]
            ==
            district
        )
    ]

    if result.empty:
        return None

    row = result.iloc[0]

    return {

        "source1":
        row["Supplier_District_1"],

        "source2":
        row["Supplier_District_2"],

        "source3":
        row["Supplier_District_3"]

    }