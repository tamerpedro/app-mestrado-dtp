from __future__ import annotations

import csv
from pathlib import Path

from .models import RiskItem


def _split_list(value: str) -> list[str]:
    return [item.strip().lower() for item in (value or "").split(";") if item.strip()]


def load_risks(path: str | Path) -> list[RiskItem]:
    risks: list[RiskItem] = []
    with Path(path).open("r", encoding="utf-8", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            risks.append(
                RiskItem(
                    id=row["id"],
                    titulo=row["titulo"],
                    categoria=row.get("categoria", "planejamento"),
                    tipo_contratacao=_split_list(row["tipo_contratacao"]),
                    palavras_chave=_split_list(row["palavras_chave"]),
                    causa=row["causa"],
                    consequencia=row["consequencia"],
                    probabilidade_padrao=row["probabilidade_padrao"],
                    impacto_padrao=row["impacto_padrao"],
                    acao_preventiva=row["acao_preventiva"],
                    acao_contingencia=row["acao_contingencia"],
                    responsavel_sugerido=row["responsavel_sugerido"],
                )
            )
    return risks
