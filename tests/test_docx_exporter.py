from zipfile import ZipFile

from src.docx_exporter import to_docx
from src.models import ContractContext, MatrixRow


def test_docx_export_contains_risk_map_structure():
    context = ContractContext(
        objeto="Aquisição de solução de TIC",
        tipo_contratacao="aquisicao",
        area_demandante="DETC",
        valor_estimado=1000,
        criticidade="media",
        prazo="12 meses",
        modalidade="pregao",
        contexto="Contratação de TIC",
    )
    rows = [
        MatrixRow(
            id="R001",
            risco="Especificação técnica insuficiente",
            categoria="planejamento",
            causa="Levantamento incompleto",
            consequencia="Contratação inadequada",
            probabilidade="3-Média",
            impacto="4-Alto",
            nivel="alto",
            estrategia="Mitigar",
            acao_preventiva="Validar requisitos",
            acao_contingencia="Revisar especificações",
            responsavel="Equipe de planejamento",
        )
    ]

    content = to_docx(rows, context)

    with ZipFile(__import__("io").BytesIO(content)) as archive:
        document_xml = archive.read("word/document.xml").decode("utf-8")

    assert "MAPA DE GERENCIAMENTO DE RISCOS" in document_xml
    assert "Riscos do Planejamento" in document_xml
    assert "AÇÕES PREVENTIVAS" in document_xml
