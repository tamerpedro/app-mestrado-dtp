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


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as csvfile:
        reader = csv.reader(csvfile)
        try:
            headers = [_normalize_header(field) for field in next(reader)]
        except StopIteration:
            raise ValueError("Biblioteca de riscos vazia.") from None

        missing = [field for field in FIELDNAMES if field not in headers]
        if missing:
            raise ValueError(f"Colunas obrigatorias ausentes na biblioteca de riscos: {', '.join(missing)}")

        rows: list[dict[str, str]] = []
        for values in reader:
            if not any((value or "").strip() for value in values):
                continue
            row = {header: values[index] if index < len(values) else "" for index, header in enumerate(headers)}
            rows.append(row)
        return rows


def _required_row_value(row: dict[str, str], field: str, line_number: int) -> str:
    value = row.get(field, "")
    if value is None:
        value = ""
    value = value.strip()
    if value:
        return value
    raise ValueError(f"Valor obrigatorio ausente na coluna '{field}', linha {line_number}.")


def _optional_row_value(row: dict[str, str], field: str, default: str = "") -> str:
    value = row.get(field, default)
    if value is None:
        return default
    return value.strip() or default


def load_risks(path: str | Path) -> list[RiskItem]:
    risks: list[RiskItem] = []
    for index, row in enumerate(_read_csv_rows(Path(path)), start=2):
        risks.append(
            RiskItem(
                id=_required_row_value(row, "id", index),
                titulo=_required_row_value(row, "titulo", index),
                categoria=_optional_row_value(row, "categoria", "planejamento"),
                tipo_contratacao=_split_list(_required_row_value(row, "tipo_contratacao", index)),
                palavras_chave=_split_list(_optional_row_value(row, "palavras_chave")),
                causa=_required_row_value(row, "causa", index),
                consequencia=_required_row_value(row, "consequencia", index),
                probabilidade_padrao=_required_row_value(row, "probabilidade_padrao", index),
                impacto_padrao=_required_row_value(row, "impacto_padrao", index),
                acao_preventiva=_required_row_value(row, "acao_preventiva", index),
                acao_contingencia=_required_row_value(row, "acao_contingencia", index),
                responsavel_sugerido=_required_row_value(row, "responsavel_sugerido", index),
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
    return _read_csv_rows(path)


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
