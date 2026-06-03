from src.scoring import risk_level, risk_score


def test_risk_score_multiplies_probability_and_impact():
    assert risk_score("3-Média", "4-Alto") == 12


def test_risk_level_classifies_high_risk():
    assert risk_level("3-Média", "4-Alto") == "alto"


def test_risk_level_accepts_accents():
    assert risk_level("média", "médio") == "alto"
