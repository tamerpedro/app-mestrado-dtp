from src.domain import (
    ACTION_STATUS_LABELS,
    CATEGORY_LABELS,
    CATEGORIES,
    MODALITIES,
    MODALITY_LABELS,
    STRATEGIES,
    STRATEGY_LABELS,
    parse_action_status,
    parse_scale,
    parse_strategy,
    probability_label,
)
from src.exporters import row_to_export_dict, to_csv
from src.models import ActionItem, MatrixRow


def test_parse_scale_accepts_numbers_and_legacy_labels():
    assert parse_scale(4) == 4
    assert parse_scale("4") == 4
    assert parse_scale("4-Alta") == 4
    assert parse_scale("média") == 3
    assert parse_scale("Muito Alto") == 5
    assert parse_scale("9") == 0
    assert parse_scale("") == 0


def test_parse_codes_accept_legacy_portuguese_labels():
    assert parse_strategy("Mitigar") == "mitigate"
    assert parse_strategy("compartilhar") == "share"
    assert parse_strategy("") == "mitigate"
    assert parse_action_status("Não iniciado") == "not_started"
    assert parse_action_status("Concluído") == "completed"


def test_every_code_has_a_label():
    assert set(STRATEGIES) == set(STRATEGY_LABELS)
    assert set(CATEGORIES) == set(CATEGORY_LABELS)
    assert set(MODALITIES) == set(MODALITY_LABELS)
    assert probability_label(3) == "3-Média"


def _row() -> MatrixRow:
    return MatrixRow(
        id="R001",
        risco="Risco",
        categoria="selecao",
        causa="Causa",
        consequencias=["Consequencia"],
        probabilidade=5,
        impacto=4,
        nivel="critical",
        estrategia="share",
        acoes_preventivas=[ActionItem("Prevenir", situacao="in_progress", responsavel="Equipe")],
        acoes_contingencia=[ActionItem("Contingenciar")],
    )


def test_exports_show_labels_not_codes():
    data = row_to_export_dict(_row())

    assert data["probabilidade"] == "5-Muito Alta"
    assert data["impacto"] == "4-Alto"
    assert data["nivel"] == "Crítico"
    assert data["estrategia"] == "Compartilhar"
    assert data["categoria"] == "Seleção de fornecedor"
    assert data["acao_preventiva"] == "Prevenir (Iniciado - Equipe)"
    assert data["acao_contingencia"] == "Contingenciar (Não iniciado)"
    assert "critical" not in to_csv([_row()])
