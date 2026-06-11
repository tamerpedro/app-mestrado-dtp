from pathlib import Path
from uuid import uuid4

from src.library_writer import save_matrix_row_to_library
from src.models import ActionItem, ContractContext, MatrixRow
from src.risk_library import load_risks


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


def test_save_matrix_row_to_library_reloads_as_risk_item():
    path = Path(f".test_riscos_library_{uuid4().hex}.csv")
    context = ContractContext(
        objeto="Contratacao de software",
        tipo_contratacao="software",
        area_demandante="TI",
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
        probabilidade="3-Média",
        impacto="4-Alto",
        nivel="alto",
        estrategia="Mitigar",
        acoes_preventivas=[ActionItem("Mapear interfaces", responsavel="Equipe tecnica")],
        acoes_contingencia=[ActionItem("Acionar plano de rollback", responsavel="Equipe tecnica")],
        responsavel="Equipe tecnica",
        tags=["manual"],
    )

    result = save_matrix_row_to_library(path, row, context)
    risks = load_risks(path)

    assert result.saved is True
    assert risks[0].id == "R001"
    assert risks[0].titulo == "Falha de integracao"
    assert risks[0].tipo_contratacao == ["software"]
