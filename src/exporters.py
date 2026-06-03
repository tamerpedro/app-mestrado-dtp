from __future__ import annotations

import csv
import io
from dataclasses import asdict

from .models import MatrixRow


EXPORT_FIELDS = [
    "id",
    "risco",
    "causa",
    "consequencia",
    "probabilidade",
    "impacto",
    "nivel",
    "acao_preventiva",
    "acao_contingencia",
    "responsavel",
    "justificativa",
]


def selected_rows(rows: list[MatrixRow]) -> list[MatrixRow]:
    return [row for row in rows if row.selecionado]


def to_csv(rows: list[MatrixRow]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=EXPORT_FIELDS)
    writer.writeheader()
    for row in selected_rows(rows):
        data = asdict(row)
        writer.writerow({field: data[field] for field in EXPORT_FIELDS})
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
                    _latex_escape(row.probabilidade),
                    _latex_escape(row.impacto),
                    _latex_escape(row.nivel),
                    _latex_escape(row.acao_preventiva),
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
