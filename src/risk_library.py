from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from .domain import impact_label, parse_category, parse_scale, probability_label
from .i18n import DEFAULT_LANGUAGE, normalize_language
from .models import TRANSLATABLE_FIELDS, ContractContext, MatrixRow, RiskItem


BASE_FIELDNAMES = [
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

# Colunas de traducao (opcionais): "<campo>_<idioma>". A biblioteca antiga, sem
# elas, continua carregando; o texto em PT serve de fallback e vice-versa.
TRANSLATION_LANGUAGES = ["en"]
TRANSLATION_FIELDNAMES = [
    f"{field}_{lang}"
    for lang in TRANSLATION_LANGUAGES
    for field in [*TRANSLATABLE_FIELDS, "palavras_chave"]
]
FIELDNAMES = [*BASE_FIELDNAMES, *TRANSLATION_FIELDNAMES]
REQUIRED_TEXT_FIELDS = ["titulo", "causa", "consequencia", "acao_preventiva", "acao_contingencia"]


@dataclass(frozen=True)
class LibrarySaveResult:
    saved: bool
    risk_id: str
    message: str
    detail: str = ""


def _split_list(value: str) -> list[str]:
    return [item.strip().lower() for item in (value or "").split(";") if item.strip()]


def _normalize_header(value: str | None) -> str:
    return (value or "").lstrip("\ufeff").strip().lower()


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    return _read_csv(path)[1]


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as csvfile:
        reader = csv.reader(csvfile)
        try:
            headers = [_normalize_header(field) for field in next(reader)]
        except StopIteration:
            raise ValueError("Biblioteca de riscos vazia.") from None

        missing = [field for field in BASE_FIELDNAMES if field not in headers]
        if missing:
            raise ValueError(f"Colunas obrigatorias ausentes na biblioteca de riscos: {', '.join(missing)}")

        rows: list[dict[str, str]] = []
        for values in reader:
            if not any((value or "").strip() for value in values):
                continue
            row = {header: values[index] if index < len(values) else "" for index, header in enumerate(headers)}
            rows.append(row)
        return headers, rows


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


def _required_scale_value(row: dict[str, str], field: str, line_number: int) -> int:
    raw = _required_row_value(row, field, line_number)
    value = parse_scale(raw)
    if not value:
        raise ValueError(f"Valor invalido '{raw}' na coluna '{field}', linha {line_number}: use 1 a 5.")
    return value


def _translations(row: dict[str, str]) -> dict[str, dict[str, str]]:
    translations: dict[str, dict[str, str]] = {}
    for lang in TRANSLATION_LANGUAGES:
        texts = {field: _optional_row_value(row, f"{field}_{lang}") for field in TRANSLATABLE_FIELDS}
        texts = {field: text for field, text in texts.items() if text}
        if texts:
            translations[lang] = texts
    return translations


def _check_required_texts(row: dict[str, str], translations: dict[str, dict[str, str]], line_number: int) -> None:
    for field in REQUIRED_TEXT_FIELDS:
        if _optional_row_value(row, field) or any(field in texts for texts in translations.values()):
            continue
        raise ValueError(f"Valor obrigatorio ausente na coluna '{field}' (ou '{field}_en'), linha {line_number}.")


def load_risks(path: str | Path) -> list[RiskItem]:
    risks: list[RiskItem] = []
    for index, row in enumerate(_read_csv_rows(Path(path)), start=2):
        translations = _translations(row)
        _check_required_texts(row, translations, index)
        risks.append(
            RiskItem(
                id=_required_row_value(row, "id", index),
                titulo=_optional_row_value(row, "titulo"),
                categoria=parse_category(_optional_row_value(row, "categoria")),
                tipo_contratacao=_split_list(_required_row_value(row, "tipo_contratacao", index)),
                palavras_chave=_split_list(_optional_row_value(row, "palavras_chave")),
                causa=_optional_row_value(row, "causa"),
                consequencia=_optional_row_value(row, "consequencia"),
                probabilidade_padrao=_required_scale_value(row, "probabilidade_padrao", index),
                impacto_padrao=_required_scale_value(row, "impacto_padrao", index),
                acao_preventiva=_optional_row_value(row, "acao_preventiva"),
                acao_contingencia=_optional_row_value(row, "acao_contingencia"),
                responsavel_sugerido=_optional_row_value(row, "responsavel_sugerido"),
                palavras_chave_en=_split_list(_optional_row_value(row, "palavras_chave_en")),
                traducoes=translations,
            )
        )
    return risks


def save_matrix_row_to_library(
    path: str | Path,
    row: MatrixRow,
    context: ContractContext,
    lang: str = DEFAULT_LANGUAGE,
) -> LibrarySaveResult:
    """Grava o risco nas colunas do idioma em que foi escrito; as do outro idioma ficam vazias."""
    target = Path(path)
    lang = normalize_language(lang)
    headers, existing_rows = _read_csv(target) if target.exists() else ([], [])
    existing = _find_existing_row(existing_rows, row, context)
    if existing:
        return LibrarySaveResult(False, existing["id"], "Este risco ja existe na biblioteca.")

    risk_id = _next_library_id(existing_rows)
    suffix = "" if lang == DEFAULT_LANGUAGE else f"_{lang}"
    texts = {
        "titulo": row.risco.strip(),
        "causa": row.causa.strip(),
        "consequencia": row.consequencia,
        "acao_preventiva": row.acao_preventiva,
        "acao_contingencia": row.acao_contingencia,
        "palavras_chave": _build_keywords(row, context),
    }
    library_row = {field: "" for field in FIELDNAMES}
    library_row.update(
        {
            "id": risk_id,
            "categoria": row.categoria,
            "tipo_contratacao": context.tipo_contratacao.strip().lower(),
            "probabilidade_padrao": probability_label(row.probabilidade),
            "impacto_padrao": impact_label(row.impacto),
        }
    )
    library_row.update({f"{field}{suffix}": text for field, text in texts.items()})

    try:
        if existing_rows and set(FIELDNAMES) <= set(headers):
            with target.open("a", encoding="utf-8", newline="") as csvfile:
                csv.DictWriter(csvfile, fieldnames=headers, lineterminator=_line_ending(target)).writerow(
                    {header: library_row.get(header, "") for header in headers}
                )
        else:
            _rewrite_library(target, [*existing_rows, library_row])
    except OSError as exc:
        return LibrarySaveResult(False, "", f"Nao foi possivel salvar na biblioteca: {exc}", detail=str(exc))

    return LibrarySaveResult(True, risk_id, "Risco salvo na biblioteca.")


def _line_ending(path: Path) -> str:
    if not path.exists():
        return "\r\n"
    with path.open("rb") as handle:
        return "\r\n" if b"\r\n" in handle.read(4096) else "\n"


def _rewrite_library(path: Path, rows: list[dict[str, str]]) -> None:
    """Reescreve a biblioteca com todas as colunas (usado para migrar o formato antigo)."""
    line_ending = _line_ending(path)
    with path.open("w", encoding="utf-8-sig", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES, lineterminator=line_ending, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDNAMES})


def _find_existing_row(
    existing_rows: list[dict[str, str]],
    row: MatrixRow,
    context: ContractContext,
) -> dict[str, str] | None:
    title = row.risco.strip().lower()
    contract_type = context.tipo_contratacao.strip().lower()
    title_columns = ["titulo", *(f"titulo_{lang}" for lang in TRANSLATION_LANGUAGES)]
    for existing in existing_rows:
        existing_types = _split_list(existing.get("tipo_contratacao", ""))
        existing_titles = {(existing.get(column) or "").strip().lower() for column in title_columns}
        if title in existing_titles and contract_type in existing_types:
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
