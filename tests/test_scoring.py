from src.scoring import canonical_scale, risk_level, risk_score


def test_risk_score_multiplies_probability_and_impact():
    assert risk_score(3, 4) == 12


def test_risk_level_classifies_high_risk():
    assert risk_level(3, 4) == "high"


def test_risk_level_boundaries():
    assert risk_level(1, 3) == "low"
    assert risk_level(2, 2) == "moderate"
    assert risk_level(2, 4) == "high"
    assert risk_level(3, 5) == "critical"
    assert risk_level(0, 5) == "undefined"


def test_risk_level_accepts_legacy_labels_with_accents():
    assert risk_level("3-Média", "4-Alto") == "high"
    assert risk_level("média", "médio") == "high"


def test_canonical_scale_defaults_to_medium():
    assert canonical_scale("4-Alta") == 4
    assert canonical_scale("desconhecido") == 3
