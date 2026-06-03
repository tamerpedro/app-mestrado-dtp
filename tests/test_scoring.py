from src.scoring import risk_level, risk_score


def test_risk_score_multiplies_probability_and_impact():
    assert risk_score("media", "alto") == 6


def test_risk_level_classifies_high_risk():
    assert risk_level("alta", "alto") == "alto"


def test_risk_level_accepts_accents():
    assert risk_level("média", "médio") == "medio"
