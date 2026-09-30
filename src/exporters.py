from __future__ import annotations

import csv
import io

from .domain import action_status_label, category_label, impact_label, probability_label, risk_level_label, strategy_label
from .models import ActionItem, MatrixRow


EXPORT_FIELDS = [
    "id",
    "risco",
    "categoria",
    "causa",
    "consequencia",
    "probabilidade",
    "impacto",
    "nivel",
    "estrategia",
    "acao_preventiva",
    "acao_contingencia",
    "justificativa",
]


def selected_rows(rows: list[MatrixRow]) -> list[MatrixRow]:
    return [row for row in rows if row.selecionado]


def row_to_export_dict(row: MatrixRow) -> dict[str, str]:
    return {
        "id": row.id,
        "risco": row.risco,
        "categoria": category_label(row.categoria),
        "causa": row.causa,
        "consequencia": _join_text_items(row.consequencias),
        "probabilidade": probability_label(row.probabilidade),
        "impacto": impact_label(row.impacto),
        "nivel": risk_level_label(row.nivel),
        "estrategia": strategy_label(row.estrategia),
        "acao_preventiva": _join_action_items(row.acoes_preventivas),
        "acao_contingencia": _join_action_items(row.acoes_contingencia),
        "justificativa": row.justificativa,
    }


def to_csv(rows: list[MatrixRow]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=EXPORT_FIELDS)
    writer.writeheader()
    for row in selected_rows(rows):
        writer.writerow(row_to_export_dict(row))
    return output.getvalue()


def to_latex(rows: list[MatrixRow]) -> str:
    lines = [
        r"\begin{longtable}{p{0.08\textwidth}p{0.22\textwidth}p{0.12\textwidth}p{0.12\textwidth}p{0.12\textwidth}p{0.28\textwidth}}",
        r"\textbf{ID} & \textbf{Risco} & \textbf{Prob.} & \textbf{Impacto} & \textbf{Nivel} & \textbf{Acao preventiva} \\",
        r"\hline",
    ]
    for row in selected_rows(rows):
        lines.append(
            " & ".join(
                [
                    _latex_escape(row.id),
                    _latex_escape(row.risco),
                    _latex_escape(probability_label(row.probabilidade)),
                    _latex_escape(impact_label(row.impacto)),
                    _latex_escape(risk_level_label(row.nivel)),
                    _latex_escape(_join_action_items(row.acoes_preventivas)),
                ]
            )
            + r" \\"
        )
    lines.append(r"\end{longtable}")
    return "\n".join(lines)


def _latex_escape(value: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
    }
    text = str(value or "")
    for source, target in replacements.items():
        text = text.replace(source, target)
    return text


def _join_text_items(items: list[str]) -> str:
    return "; ".join(item.strip() for item in items if item and item.strip())


def _join_action_items(actions: list[ActionItem]) -> str:
    formatted = []
    for action in actions:
        description = (action.descricao or "").strip()
        if not description:
            continue
        metadata = " - ".join(
            item.strip()
            for item in [action_status_label(action.situacao), action.responsavel]
            if item and item.strip()
        )
        formatted.append(f"{description} ({metadata})" if metadata else description)
    return "; ".join(formatted)
