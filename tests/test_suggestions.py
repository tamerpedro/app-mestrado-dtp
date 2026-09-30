from collections import Counter

from src.models import ContractContext, RiskItem
from src.risk_library import load_risks
from src.suggestions import suggest_risks, suggestion_score


def test_suggest_risks_uses_contract_context():
    context = ContractContext(
        objeto="Aquisicao de solucao de software com requisitos de seguranca",
        tipo_contratacao="software",
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
    assert all(action.responsavel == "" for row in suggestions for action in row.acoes_preventivas)
    assert all(action.responsavel == "" for row in suggestions for action in row.acoes_contingencia)


def test_suggest_risks_limits_two_per_category():
    context = ContractContext(
        objeto="Contratacao de licencas Microsoft 365 Copilot com subscricao, creditos e controle de acesso",
        tipo_contratacao="software",
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
        valor_estimado=100000,
        criticidade="baixa",
        prazo="12 meses",
        modalidade="pregao eletronico",
        contexto="Apoio administrativo generico.",
    )
    risks = load_risks("data/riscos_base.csv")
    software_risk = next(risk for risk in risks if risk.id == "R059")

    assert suggestion_score(software_risk, context) < 2



def _synthetic_risk(impacto: int) -> RiskItem:
    return RiskItem(
        id="T001",
        titulo="Risco sintetico",
        categoria="planejamento",
        tipo_contratacao=["software"],
        palavras_chave=["homologacao"],
        causa="x",
        consequencia="y",
        probabilidade_padrao=3,
        impacto_padrao=impacto,
        acao_preventiva="p",
        acao_contingencia="c",
        responsavel_sugerido="",
    )


def test_high_criticality_adds_bonus_only_to_high_impact_risks():
    context = ContractContext(
        objeto="Homologacao de software",
        tipo_contratacao="software",
        valor_estimado=100000,
        criticidade="alta",
        prazo="12 meses",
        modalidade="pregao eletronico",
        contexto="",
    )

    medium = suggestion_score(_synthetic_risk(3), context)

    assert suggestion_score(_synthetic_risk(4), context) == medium + 1
    assert suggestion_score(_synthetic_risk(5), context) == medium + 1


def test_suggestions_are_the_same_in_both_languages():
    context = ContractContext(
        objeto="Aquisicao de solucao de software com requisitos de seguranca",
        tipo_contratacao="software",
        valor_estimado=100000,
        criticidade="alta",
        prazo="12 meses",
        modalidade="pregao",
        contexto="A contratacao exige seguranca, requisitos e homologacao tecnica.",
    )
    risks = load_risks("data/riscos_base.csv")

    pt = suggest_risks(risks, context, lang="pt")
    en = suggest_risks(risks, context, lang="en")

    assert [row.id for row in pt] == [row.id for row in en]
    r006 = next(row for row in en if row.id == "R006")
    assert r006.risco == "Information security risk"
    assert r006.acoes_preventivas[0].descricao.startswith("Include security")
