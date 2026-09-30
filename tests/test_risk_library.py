from pathlib import Path
from uuid import uuid4

import pytest

from src.models import ActionItem, ContractContext, MatrixRow
from src.risk_library import load_risks, save_matrix_row_to_library


def test_load_risks_accepts_utf8_sig_header():
    path = Path(f".test_riscos_bom_{uuid4().hex}.csv")
    path.write_text(
        "\ufeffid,titulo,categoria,tipo_contratacao,palavras_chave,causa,consequencia,"
        "probabilidade_padrao,impacto_padrao,acao_preventiva,acao_contingencia,responsavel_sugerido\n"
        "R001,Risco teste,planejamento,software,requisitos,Causa,Consequencia,"
        "3-Média,4-Alto,Prevenir,Contingenciar,Equipe\n",
        encoding="utf-8",
    )

    risks = load_risks(path)

    assert risks[0].id == "R001"
    assert risks[0].titulo == "Risco teste"
    assert risks[0].probabilidade_padrao == 3
    assert risks[0].impacto_padrao == 4


def test_save_matrix_row_to_library_reloads_as_risk_item():
    path = Path(f".test_riscos_library_{uuid4().hex}.csv")
    context = ContractContext(
        objeto="Contratacao de software",
        tipo_contratacao="software",
        valor_estimado=1000,
        criticidade="media",
        prazo="12 meses",
        modalidade="pregao",
        contexto="Sistema corporativo",
    )
    row = MatrixRow(
        id="MAN001",
        risco="Falha de integracao",
        categoria="solucao",
        causa="Interfaces nao mapeadas",
        consequencias=["Indisponibilidade parcial"],
        probabilidade=3,
        impacto=4,
        nivel="high",
        estrategia="mitigate",
        acoes_preventivas=[ActionItem("Mapear interfaces", responsavel="Equipe tecnica")],
        acoes_contingencia=[ActionItem("Acionar plano de rollback", responsavel="Equipe tecnica")],
        tags=["manual"],
    )

    result = save_matrix_row_to_library(path, row, context)
    risks = load_risks(path)

    assert result.saved is True
    assert risks[0].id == "R001"
    assert risks[0].titulo == "Falha de integracao"
    assert risks[0].tipo_contratacao == ["software"]
    assert risks[0].responsavel_sugerido == ""
    assert (risks[0].probabilidade_padrao, risks[0].impacto_padrao) == (3, 4)
    assert "3-Média" in path.read_text(encoding="utf-8")


def test_load_risks_rejects_invalid_scale():
    path = Path(f".test_riscos_invalid_{uuid4().hex}.csv")
    path.write_text(
        "id,titulo,categoria,tipo_contratacao,palavras_chave,causa,consequencia,"
        "probabilidade_padrao,impacto_padrao,acao_preventiva,acao_contingencia,responsavel_sugerido\n"
        "R001,Risco teste,planejamento,software,requisitos,Causa,Consequencia,"
        "9,4-Alto,Prevenir,Contingenciar,Equipe\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="probabilidade_padrao"):
        load_risks(path)


def test_base_library_loads_with_numeric_scales():
    risks = load_risks("data/riscos_base.csv")

    assert len(risks) == 62
    assert all(risk.probabilidade_padrao in range(1, 6) for risk in risks)
    assert all(risk.impacto_padrao in range(1, 6) for risk in risks)
