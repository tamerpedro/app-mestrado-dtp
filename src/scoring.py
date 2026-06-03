SCORES = {
    "baixa": 1,
    "media": 2,
    "alta": 3,
    "baixo": 1,
    "medio": 2,
    "alto": 3,
}


def normalize_level(value: str) -> str:
    value = (value or "").strip().lower()
    replacements = {
        "média": "media",
        "medio": "medio",
        "médio": "medio",
    }
    return replacements.get(value, value)


def risk_score(probabilidade: str, impacto: str) -> int:
    probability = SCORES.get(normalize_level(probabilidade), 0)
    impact = SCORES.get(normalize_level(impacto), 0)
    return probability * impact


def risk_level(probabilidade: str, impacto: str) -> str:
    score = risk_score(probabilidade, impacto)
    if score >= 6:
        return "alto"
    if score >= 3:
        return "medio"
    if score >= 1:
        return "baixo"
    return "indefinido"
