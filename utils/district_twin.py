from utils.crop_engine import rank_crops
from utils.scarcity_engine import predict_shortages


def build_twin(district, risk_data, profiles=None, water_risk=None):
    scenario = dict(risk_data) if water_risk is None else dict(risk_data, WaterRisk=water_risk)
    return {
        "district": district,
        "risks": scenario,
        "best_crops": rank_crops(district, scenario, profiles),
        "shortages": predict_shortages(scenario),
    }
