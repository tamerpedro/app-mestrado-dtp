"""Codigos de dominio e rotulos de exibicao.

Os codigos (inteiros 1-5 e identificadores ASCII) sao o que o app calcula,
filtra e guarda em ``st.session_state``. Os rotulos vem dos catalogos de
idioma (``locales/*.json``) via ``src.i18n.t``.
"""

from __future__ import annotations

import unicodedata

from .i18n import DEFAULT_LANGUAGE, LANGUAGES, t

# Escalas de probabilidade e impacto: pesos 1-5.
SCALE_VALUES = [1, 2, 3, 4, 5]

# Nivel de risco = probabilidade x impacto.
RISK_LEVELS = ["low", "moderate", "high", "critical"]
RISK_LEVEL_UNDEFINED = "undefined"

STRATEGIES = ["mitigate", "accept", "share", "avoid"]
DEFAULT_STRATEGY = "mitigate"

ACTION_STATUSES = ["not_started", "in_progress", "completed"]
DEFAULT_ACTION_STATUS = "not_started"

CATEGORIES = ["planejamento", "selecao", "gestao", "solucao", "instalacao", "cronograma"]
DEFAULT_CATEGORY = "planejamento"

CONTRACT_TYPES = ["aquisicao", "servico", "software"]

CRITICALITIES = ["baixa", "media", "alta"]

MODALITIES = [
    "dispensa_valor",
    "inexigibilidade",
    "pregao",
    "pregao_poc",
    "pregao_consulta",
    "pregao_consulta_poc",
]
DEFAULT_MODALITY = "pregao"


# --------------------------------------------------------------------------
# Normalizacao de valores vindos do CSV ou de versoes anteriores do app
# --------------------------------------------------------------------------

def _fold(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    return "".join(char for char in normalized if not unicodedata.combining(char)).strip().lower()


_SCALE_WORDS = {
    "muito baixa": 1,
    "muito baixo": 1,
    "baixa": 2,
    "baixo": 2,
    "media": 3,
    "medio": 3,
    "alta": 4,
    "alto": 4,
    "muito alta": 5,
    "muito alto": 5,
}


def parse_scale(value: int | str | None) -> int:
    """Converte "3", 3, "3-Média" ou "média" no peso 1-5; 0 se nao reconhecido."""
    if isinstance(value, int):
        return value if value in SCALE_VALUES else 0
    text = (value or "").strip()
    if text[:1].isdigit():
        number = int(text[0])
        return number if number in SCALE_VALUES else 0
    return _SCALE_WORDS.get(_fold(text), 0)


def _parse_code(value: str | None, codes: list[str], prefix: str, default: str) -> str:
    folded = _fold(value or "")
    if not folded:
        return default
    for code in codes:
        if folded == code or any(folded == _fold(t(f"{prefix}.{code}", lang)) for lang in LANGUAGES):
            return code
    return default


def parse_strategy(value: str | None) -> str:
    return _parse_code(value, STRATEGIES, "strategy", DEFAULT_STRATEGY)


def parse_action_status(value: str | None) -> str:
    return _parse_code(value, ACTION_STATUSES, "status", DEFAULT_ACTION_STATUS)


def parse_category(value: str | None) -> str:
    folded = _fold(value or "")
    return folded or DEFAULT_CATEGORY


# --------------------------------------------------------------------------
# Rotulos de exibicao
# --------------------------------------------------------------------------

def probability_label(value: int, lang: str = DEFAULT_LANGUAGE) -> str:
    return f"{value}-{t(f'probability.{value}', lang)}" if value in SCALE_VALUES else ""


def impact_label(value: int, lang: str = DEFAULT_LANGUAGE) -> str:
    return f"{value}-{t(f'impact.{value}', lang)}" if value in SCALE_VALUES else ""


def risk_level_label(code: str, lang: str = DEFAULT_LANGUAGE) -> str:
    code = code if code in RISK_LEVELS else RISK_LEVEL_UNDEFINED
    return t(f"level.{code}", lang)


def risk_level_range_label(code: str, lang: str = DEFAULT_LANGUAGE) -> str:
    return t(f"level.range.{code}", lang)


def _label(prefix: str, code: str, codes: list[str], lang: str) -> str:
    return t(f"{prefix}.{code}", lang) if code in codes else (code or "")


def strategy_label(code: str, lang: str = DEFAULT_LANGUAGE) -> str:
    return _label("strategy", code, STRATEGIES, lang)


def action_status_label(code: str, lang: str = DEFAULT_LANGUAGE) -> str:
    return _label("status", code, ACTION_STATUSES, lang)


def category_label(code: str, lang: str = DEFAULT_LANGUAGE) -> str:
    code = code or DEFAULT_CATEGORY
    return t(f"category.{code}", lang) if code in CATEGORIES else code.title()


def contract_type_label(code: str, lang: str = DEFAULT_LANGUAGE) -> str:
    return t(f"contract_type.{code}", lang) if code in CONTRACT_TYPES else code.title()


def criticality_label(code: str, lang: str = DEFAULT_LANGUAGE) -> str:
    return t(f"criticality.{code}", lang) if code in CRITICALITIES else code.title()


def modality_label(code: str, lang: str = DEFAULT_LANGUAGE) -> str:
    return _label("modality", code, MODALITIES, lang)
