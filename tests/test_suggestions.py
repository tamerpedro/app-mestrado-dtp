from src.models import ContractContext
from src.risk_library import load_risks
from src.suggestions import suggest_risks


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
