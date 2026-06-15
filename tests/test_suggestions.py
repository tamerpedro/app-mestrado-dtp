from collections import Counter

from src.models import ContractContext
from src.risk_library import load_risks
from src.suggestions import suggest_risks, suggestion_score


def test_suggest_risks_uses_contract_context():
    context = ContractContext(
        objeto="Aquisicao de solucao de software com requisitos de seguranca",
        tipo_contratacao="software",
        area_demandante="TI",
        valor_estimado=100000,
        criticidade="alta",
        prazo="12 meses",
        modalidade="pregao eletronico",
        contexto="A contratacao exige seguranca, requisitos e homologacao tecnica.",
    )
    risks = load_risks("data/riscos_base.csv")

    suggestions = suggest_risks(risks, context)

    assert suggestions
    assert any(row.id == "R006" for row in suggestions)


def test_suggest_risks_limits_two_per_category():
    context = ContractContext(
        objeto="Contratacao de licencas Microsoft 365 Copilot com subscricao, creditos e controle de acesso",
        tipo_contratacao="software",
        area_demandante="TI",
        valor_estimado=100000,
        criticidade="alta",
        prazo="12 meses",
        modalidade="pregao eletronico",
        contexto="Licenciamento, compliance, seguranca, subscricao e uso de dados sensiveis.",
    )
    risks = load_risks("data/riscos_base.csv")

    suggestions = suggest_risks(risks, context)
    counts = Counter(row.categoria for row in suggestions)

    assert suggestions
    assert all(count <= 2 for count in counts.values())


def test_contract_type_alone_is_not_enough_to_suggest_risk():
    context = ContractContext(
        objeto="Contratacao de solucao de TIC",
        tipo_contratacao="software",
        area_demandante="TI",
        valor_estimado=100000,
        criticidade="baixa",
        prazo="12 meses",
        modalidade="pregao eletronico",
        contexto="Apoio administrativo generico.",
    )
    risks = load_risks("data/riscos_base.csv")
    software_risk = next(risk for risk in risks if risk.id == "R059")

    assert suggestion_score(software_risk, context) < 2
