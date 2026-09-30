"""Codigos de dominio e rotulos de exibicao.

Os codigos (inteiros 1-5 e identificadores ASCII) sao o que o app calcula,
filtra e guarda em ``st.session_state``. Os rotulos sao apenas exibicao e,
na fase 2 da internacionalizacao, passam a vir dos arquivos de idioma.
"""

from __future__ import annotations

import unicodedata

# Escalas de probabilidade e impacto: pesos 1-5.
SCALE_VALUES = [1, 2, 3, 4, 5]

PROBABILITY_LABELS = {
    1: "Muito Baixa",
    2: "Baixa",
    3: "Média",
    4: "Alta",
    5: "Muito Alta",
}

IMPACT_LABELS = {
    1: "Muito Baixo",
    2: "Baixo",
    3: "Médio",
    4: "Alto",
    5: "Muito Alto",
}

# Nivel de risco = probabilidade x impacto.
RISK_LEVELS = ["low", "moderate", "high", "critical"]
RISK_LEVEL_UNDEFINED = "undefined"
RISK_LEVEL_LABELS = {
    "low": "Pequeno",
    "moderate": "Moderado",
    "high": "Alto",
    "critical": "Crítico",
    RISK_LEVEL_UNDEFINED: "Indefinido",
}
RISK_LEVEL_RANGES = {
    "low": "1 a 3",
    "moderate": "4 a 6",
    "high": "8 a 12",
    "critical": "15 a 25",
}

STRATEGIES = ["mitigate", "accept", "share", "avoid"]
STRATEGY_LABELS = {
    "mitigate": "Mitigar",
    "accept": "Aceitar",
    "share": "Compartilhar",
    "avoid": "Evitar",
}
DEFAULT_STRATEGY = "mitigate"

ACTION_STATUSES = ["not_started", "in_progress", "completed"]
ACTION_STATUS_LABELS = {
    "not_started": "Não iniciado",
    "in_progress": "Iniciado",
    "completed": "Concluído",
}
DEFAULT_ACTION_STATUS = "not_started"

CATEGORIES = ["planejamento", "selecao", "gestao", "solucao", "instalacao", "cronograma"]
DEFAULT_CATEGORY = "planejamento"
CATEGORY_LABELS = {
    "planejamento": "Planejamento",
    "selecao": "Seleção de fornecedor",
    "gestao": "Gestão do contrato",
    "solucao": "Solução",
    "instalacao": "Instalação",
    "cronograma": "Cronograma",
}

CONTRACT_TYPES = ["aquisicao", "servico", "software"]
CONTRACT_TYPE_LABELS = {
    "aquisicao": "Aquisição",
    "servico": "Serviço",
    "software": "Software",
}

CRITICALITIES = ["baixa", "media", "alta"]
CRITICALITY_LABELS = {
    "baixa": "Baixa",
    "media": "Média",
    "alta": "Alta",
}

MODALITIES = [
    "dispensa_valor",
    "inexigibilidade",
    "pregao",
    "pregao_poc",
    "pregao_consulta",
    "pregao_consulta_poc",
]
DEFAULT_MODALITY = "pregao"
MODALITY_LABELS = {
    "dispensa_valor": "Dispensa de Licitação P/ Valor",
    "inexigibilidade": "Inexigibilidade",
    "pregao": "Pregão Simples",
    "pregao_poc": "Pregão com POC",
    "pregao_consulta": "Pregão com Consulta Pública",
    "pregao_consulta_poc": "Pregão com Consulta Pública e POC",
}


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


def _parse_code(value: str | None, codes: list[str], labels: dict[str, str], default: str) -> str:
    folded = _fold(value or "")
    if not folded:
        return default
    for code in codes:
        if folded == code or folded == _fold(labels[code]):
            return code
    return default


def parse_strategy(value: str | None) -> str:
    return _parse_code(value, STRATEGIES, STRATEGY_LABELS, DEFAULT_STRATEGY)


def parse_action_status(value: str | None) -> str:
    return _parse_code(value, ACTION_STATUSES, ACTION_STATUS_LABELS, DEFAULT_ACTION_STATUS)


def parse_category(value: str | None) -> str:
    folded = _fold(value or "")
    return folded or DEFAULT_CATEGORY


# --------------------------------------------------------------------------
# Rotulos de exibicao
# --------------------------------------------------------------------------

def probability_label(value: int) -> str:
    return f"{value}-{PROBABILITY_LABELS[value]}" if value in PROBABILITY_LABELS else ""


def impact_label(value: int) -> str:
    return f"{value}-{IMPACT_LABELS[value]}" if value in IMPACT_LABELS else ""


def risk_level_label(code: str) -> str:
    return RISK_LEVEL_LABELS.get(code, RISK_LEVEL_LABELS[RISK_LEVEL_UNDEFINED])


def risk_level_range_label(code: str) -> str:
    return f"{RISK_LEVEL_RANGES[code]} - {RISK_LEVEL_LABELS[code]}"


def strategy_label(code: str) -> str:
    return STRATEGY_LABELS.get(code, code)


def action_status_label(code: str) -> str:
    return ACTION_STATUS_LABELS.get(code, code)


def category_label(code: str) -> str:
    code = code or DEFAULT_CATEGORY
    return CATEGORY_LABELS.get(code, code.title())


def contract_type_label(code: str) -> str:
    return CONTRACT_TYPE_LABELS.get(code, code.title())


def criticality_label(code: str) -> str:
    return CRITICALITY_LABELS.get(code, code.title())


def modality_label(code: str) -> str:
    return MODALITY_LABELS.get(code, code)
