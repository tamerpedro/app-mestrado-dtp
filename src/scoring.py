from __future__ import annotations

from .domain import RISK_LEVEL_UNDEFINED, parse_scale

# Opcoes dos seletores: pesos 1-5 (o rotulo vem de ``domain``).
PROBABILITY_OPTIONS = [1, 2, 3, 4, 5]
IMPACT_OPTIONS = [1, 2, 3, 4, 5]
DEFAULT_SCALE_VALUE = 3


def score_value(value: int | str | None) -> int:
    return parse_scale(value)


def risk_score(probabilidade: int | str, impacto: int | str) -> int:
    return score_value(probabilidade) * score_value(impacto)


def level_for_score(score: int) -> str:
    if score >= 15:
        return "critical"
    if score >= 8:
        return "high"
    if score >= 4:
        return "moderate"
    if score >= 1:
        return "low"
    return RISK_LEVEL_UNDEFINED


def risk_level(probabilidade: int | str, impacto: int | str) -> str:
    return level_for_score(risk_score(probabilidade, impacto))


def canonical_scale(value: int | str | None) -> int:
    """Peso 1-5 valido para os seletores; 3 quando o valor nao e reconhecido."""
    return score_value(value) or DEFAULT_SCALE_VALUE
