from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from .models import ContractContext, MatrixRow, RiskItem


FIELDNAMES = [
    "id",
    "titulo",
    "categoria",
    "tipo_contratacao",
    "palavras_chave",
    "causa",
    "consequencia",
    "probabilidade_padrao",
    "impacto_padrao",
    "acao_preventiva",
    "acao_contingencia",
    "responsavel_sugerido",
]


@dataclass(frozen=True)
class LibrarySaveResult:
    saved: bool
    risk_id: str
    message: str


def _split_list(value: str) -> list[str]:
    return [item.strip().lower() for item in (value or "").split(";") if item.strip()]


def _normalize_header(value: str | None) -> str:
    return (value or "").lstrip("\ufeff").strip().lower()


def _dict_reader(csvfile) -> csv.DictReader:
    reader = csv.DictReader(csvfile)
    reader.fieldnames = [_normalize_header(field) for field in (reader.fieldnames or [])]
    missing = [field for field in FIELDNAMES if field not in reader.fieldnames]
    if missing:
        raise ValueError(f"Colunas obrigatorias ausentes na biblioteca de riscos: {', '.join(missing)}")
    return reader


def load_risks(path: str | Path) -> list[RiskItem]:
    risks: list[RiskItem] = []
    with Path(path).open("r", encoding="utf-8-sig", newline="") as csvfile:
        reader = _dict_reader(csvfile)
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


def save_matrix_row_to_library(path: str | Path, row: MatrixRow, context: ContractContext) -> LibrarySaveResult:
    target = Path(path)
    existing_rows = _read_library_rows(target)
    existing = _find_existing_row(existing_rows, row, context)
    if existing:
        return LibrarySaveResult(False, existing["id"], "Este risco ja existe na biblioteca.")

    risk_id = _next_library_id(existing_rows)
    library_row = {
        "id": risk_id,
        "titulo": row.risco.strip(),
        "categoria": row.categoria,
        "tipo_contratacao": context.tipo_contratacao.strip().lower(),
        "palavras_chave": _build_keywords(row, context),
        "causa": row.causa.strip(),
        "consequencia": row.consequencia,
        "probabilidade_padrao": row.probabilidade,
        "impacto_padrao": row.impacto,
        "acao_preventiva": row.acao_preventiva,
        "acao_contingencia": row.acao_contingencia,
        "responsavel_sugerido": row.responsavel.strip(),
    }

    try:
        with target.open("a", encoding="utf-8", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
            if not existing_rows:
                writer.writeheader()
            writer.writerow(library_row)
    except OSError as exc:
        return LibrarySaveResult(False, "", f"Nao foi possivel salvar na biblioteca: {exc}")

    return LibrarySaveResult(True, risk_id, "Risco salvo na biblioteca.")


def _read_library_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as csvfile:
        return list(_dict_reader(csvfile))


def _find_existing_row(
    existing_rows: list[dict[str, str]],
    row: MatrixRow,
    context: ContractContext,
) -> dict[str, str] | None:
    title = row.risco.strip().lower()
    contract_type = context.tipo_contratacao.strip().lower()
    for existing in existing_rows:
        existing_types = _split_list(existing.get("tipo_contratacao", ""))
        if existing.get("titulo", "").strip().lower() == title and contract_type in existing_types:
            return existing
    return None


def _next_library_id(existing_rows: list[dict[str, str]]) -> str:
    numbers = []
    for row in existing_rows:
        risk_id = row.get("id", "")
        if risk_id.startswith("R") and risk_id[1:].isdigit():
            numbers.append(int(risk_id[1:]))
    next_number = max(numbers, default=0) + 1
    return f"R{next_number:03d}"


def _build_keywords(row: MatrixRow, context: ContractContext) -> str:
    raw_values = [row.risco, row.categoria, context.tipo_contratacao, context.objeto, *row.tags]
    keywords: list[str] = []
    for value in raw_values:
        for part in str(value or "").replace(",", " ").replace(";", " ").split():
            clean = part.strip().lower()
            if len(clean) >= 4 and clean not in keywords:
                keywords.append(clean)
    return ";".join(keywords[:12])
