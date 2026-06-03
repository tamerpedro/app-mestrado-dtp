from __future__ import annotations

from .models import ActionItem, ContractContext, MatrixRow, RiskItem
from .scoring import risk_level


def _text_blob(context: ContractContext) -> str:
    return " ".join(
        [
            context.objeto,
            context.tipo_contratacao,
            context.area_demandante,
            context.criticidade,
            context.prazo,
            context.modalidade,
            context.contexto,
        ]
    ).lower()


def suggestion_score(risk: RiskItem, context: ContractContext) -> int:
    score = 0
    blob = _text_blob(context)
    contract_type = context.tipo_contratacao.strip().lower()

    if contract_type in risk.tipo_contratacao:
        score += 3

    for keyword in risk.palavras_chave:
        if keyword and keyword in blob:
            score += 2

    if context.criticidade.strip().lower() == "alta" and risk.impacto_padrao in {"alto", "medio"}:
        score += 1

    return score


def suggest_risks(
    risks: list[RiskItem],
    context: ContractContext,
    minimum_score: int = 2,
) -> list[MatrixRow]:
    ranked = sorted(
        ((suggestion_score(risk, context), risk) for risk in risks),
        key=lambda item: item[0],
        reverse=True,
    )
    rows: list[MatrixRow] = []
    for score, risk in ranked:
        if score < minimum_score:
            continue
        rows.append(
            MatrixRow(
                id=risk.id,
                risco=risk.titulo,
                categoria=risk.categoria,
                causa=risk.causa,
                consequencias=[risk.consequencia],
                probabilidade=risk.probabilidade_padrao,
                impacto=risk.impacto_padrao,
                nivel=risk_level(risk.probabilidade_padrao, risk.impacto_padrao),
                estrategia="Mitigar",
                acoes_preventivas=[ActionItem(risk.acao_preventiva, responsavel=risk.responsavel_sugerido)],
                acoes_contingencia=[ActionItem(risk.acao_contingencia, responsavel=risk.responsavel_sugerido)],
                responsavel=risk.responsavel_sugerido,
                justificativa=f"Sugerido por aderencia ao contexto da contratacao. Pontuacao: {score}.",
                tags=risk.tipo_contratacao,
            )
        )
    return rows
