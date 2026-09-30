from __future__ import annotations

import base64
from collections import defaultdict
from html import escape
import io
from pathlib import Path

import streamlit as st
from openpyxl import Workbook

from src.docx_exporter import to_docx
from src.domain import (
    ACTION_STATUSES,
    CATEGORIES,
    CONTRACT_TYPES,
    CRITICALITIES,
    DEFAULT_MODALITY,
    MODALITIES,
    STRATEGIES,
    action_status_label,
    category_label,
    contract_type_label,
    criticality_label,
    impact_label,
    modality_label,
    probability_label,
    risk_level_label,
    strategy_label,
)
from src.i18n import DEFAULT_LANGUAGE, LANGUAGES, normalize_language, t
from src.exporters import EXPORT_FIELDS, row_to_export_dict, selected_rows, to_csv, to_latex
from src.models import ActionItem, ContractContext, MatrixRow
from src.risk_library import load_risks, save_matrix_row_to_library
from src.scoring import IMPACT_OPTIONS, PROBABILITY_OPTIONS, canonical_scale, risk_level
from src.suggestions import suggest_risks


DATA_PATH = Path("data/riscos_base.csv")
LOGO_PATH = Path("assets/dataprev-logo.png")
def resolve_language() -> str:
    """Idioma da sessao: parametro ?lang= na primeira visita, depois o seletor."""
    if "lang" not in st.session_state:
        st.session_state.lang = normalize_language(st.query_params.get("lang", DEFAULT_LANGUAGE))
    return normalize_language(st.session_state.lang)


LANG = resolve_language()
LANG_CHANGED = st.session_state.get("_rendered_lang") != LANG
st.session_state._rendered_lang = LANG


def tr(key: str, **params) -> str:
    return t(key, LANG, **params)


def label_in(label_func):
    """Adapta um rotulo de dominio ao idioma atual, para uso em format_func."""
    return lambda value: label_func(value, LANG)


def select(label: str, options: list, *, key: str, format_func, index: int = 0, **kwargs):
    """selectbox cujas opcoes acompanham o idioma sem perder o valor escolhido.

    O navegador nao redesenha o texto das opcoes quando so o ``format_func``
    muda. Por isso o widget ganha uma chave por idioma (``key@lang``) e o valor
    escolhido fica guardado em ``st.session_state[key]``, de onde o widget do
    outro idioma e reinicializado na troca.
    """
    widget_key = f"{key}@{LANG}"
    if LANG_CHANGED or widget_key not in st.session_state:
        stored = st.session_state.get(key)
        st.session_state[widget_key] = stored if stored in options else options[index]
    value = st.selectbox(label, options, format_func=format_func, key=widget_key, **kwargs)
    st.session_state[key] = value
    return value


st.set_page_config(page_title=tr("app.title"), layout="wide")


def apply_dataprev_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --dtp-blue: #005ca9;
            --dtp-blue-dark: #003c71;
            --dtp-cyan: #00a3e0;
            --dtp-green: #79b829;
            --dtp-yellow: #f5c400;
            --dtp-border: rgba(0, 163, 224, .28);
            --dtp-soft: rgba(0, 92, 169, .12);
        }

        .block-container {
            padding-top: 2.35rem;
            max-width: 1280px;
        }

        [data-testid="stSidebar"] {
            border-right: 1px solid var(--dtp-border);
        }

        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
            letter-spacing: 0;
        }

        .dtp-sidebar-brand {
            border-left: 5px solid var(--dtp-green);
            border-bottom: 1px solid var(--dtp-border);
            padding: .75rem 0 .9rem .9rem;
            margin: -.35rem 0 1.15rem 0;
        }

        .dtp-sidebar-brand strong {
            display: block;
            color: var(--dtp-cyan);
            font-size: 1.35rem;
            line-height: 1.1;
        }

        .dtp-sidebar-brand span {
            color: inherit;
            font-size: .82rem;
            opacity: .82;
        }

        .dtp-hero {
            position: relative;
            padding: 1.2rem 1.35rem 1.05rem 1.35rem;
            border: 1px solid var(--dtp-border);
            border-left: 7px solid var(--dtp-blue);
            border-radius: 8px;
            background:
                linear-gradient(90deg, rgba(0, 92, 169, .20), rgba(0, 163, 224, .07)),
                var(--dtp-soft);
            margin-bottom: 1.2rem;
        }

        .dtp-hero-main {
            display: flex;
            align-items: center;
            gap: 1.15rem;
            min-width: 0;
        }

        .dtp-logo-wrap {
            flex: 0 0 auto;
            width: clamp(72px, 9vw, 112px);
            aspect-ratio: 1.14;
            display: grid;
            place-items: center;
            padding: .45rem;
            border-radius: 8px;
            background: rgba(255, 255, 255, .92);
            box-shadow: 0 10px 24px rgba(0, 60, 113, .12);
        }

        .dtp-logo-wrap img {
            width: 100%;
            height: auto;
            display: block;
        }

        .dtp-hero-copy {
            min-width: 0;
        }

        .dtp-kicker {
            display: inline-flex;
            align-items: center;
            gap: .45rem;
            color: var(--dtp-cyan);
            font-size: .78rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: .04em;
        }

        .dtp-kicker::before {
            content: "";
            width: .7rem;
            height: .7rem;
            border-radius: 2px;
            background: linear-gradient(135deg, var(--dtp-green), var(--dtp-yellow));
        }

        .dtp-hero h1 {
            margin: .35rem 0 .25rem 0;
            font-size: clamp(2rem, 3.5vw, 3.15rem);
            line-height: 1.05;
            letter-spacing: 0;
        }

        .dtp-hero p {
            margin: 0;
            max-width: 860px;
            opacity: .86;
        }

        .dtp-status-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: .7rem;
            margin: 1rem 0 0 0;
        }

        .dtp-status {
            border-top: 3px solid var(--dtp-cyan);
            background: rgba(255, 255, 255, .045);
            border-radius: 6px;
            padding: .7rem .75rem;
            min-height: 4.3rem;
        }

        .dtp-status span {
            display: block;
            font-size: .72rem;
            opacity: .72;
            margin-bottom: .25rem;
        }

        .dtp-status strong {
            display: block;
            font-size: 1rem;
            line-height: 1.25;
        }

        .dtp-panel-title {
            display: flex;
            align-items: center;
            gap: .55rem;
            margin: .25rem 0 .75rem 0;
        }

        .dtp-panel-title::before {
            content: "";
            width: .35rem;
            height: 1.45rem;
            border-radius: 999px;
            background: var(--dtp-green);
        }

        .dtp-section-label {
            margin: 1rem 0 .35rem 0;
            padding-top: .35rem;
            border-top: 1px solid var(--dtp-border);
            color: var(--dtp-cyan);
            font-weight: 700;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: .45rem;
            border-bottom: 1px solid var(--dtp-border);
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 6px 6px 0 0;
            padding: .7rem 1rem;
            letter-spacing: 0;
        }

        .stTabs [aria-selected="true"] {
            color: var(--dtp-cyan);
            border-bottom: 3px solid var(--dtp-green);
        }

        .stButton > button,
        .stDownloadButton > button {
            border-color: var(--dtp-border);
            border-radius: 6px;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover {
            border-color: var(--dtp-cyan);
            color: var(--dtp-cyan);
        }

        [data-testid="stMetric"] {
            border-left: 4px solid var(--dtp-green);
            padding-left: .75rem;
        }

        @media (max-width: 900px) {
            .dtp-status-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }

        @media (max-width: 560px) {
            .dtp-status-grid {
                grid-template-columns: 1fr;
            }
            .dtp-hero {
                padding: 1rem;
            }
            .dtp-hero-main {
                align-items: flex-start;
                gap: .8rem;
            }
            .dtp-logo-wrap {
                width: 64px;
                padding: .35rem;
            }
            .dtp-kicker {
                font-size: .72rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_panel_title(title: str) -> None:
    st.markdown(f'<h3 class="dtp-panel-title">{escape(title)}</h3>', unsafe_allow_html=True)


def image_to_data_uri(path: Path) -> str:
    if not path.exists():
        return ""
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def render_app_header(context: ContractContext, suggested_rows: list[MatrixRow]) -> None:
    high_count = count_high_or_critical(suggested_rows)
    logo_uri = image_to_data_uri(LOGO_PATH)
    logo_html = (
        f'<div class="dtp-logo-wrap"><img src="{logo_uri}" alt="{escape(tr("app.logo_alt"))}"></div>'
        if logo_uri
        else ""
    )
    st.markdown(
        f"""
        <section class="dtp-hero">
            <div class="dtp-hero-main">
                {logo_html}
                <div class="dtp-hero-copy">
                    <div class="dtp-kicker">{escape(tr("app.kicker"))}</div>
                    <h1>{escape(tr("app.title"))}</h1>
                    <p>{escape(tr("app.subtitle"))}</p>
                </div>
            </div>
            <div class="dtp-status-grid">
                <div class="dtp-status"><span>{escape(tr("header.type"))}</span><strong>{escape(contract_type_label(context.tipo_contratacao, LANG))}</strong></div>
                <div class="dtp-status"><span>{escape(tr("header.criticality"))}</span><strong>{escape(criticality_label(context.criticidade, LANG))}</strong></div>
                <div class="dtp-status"><span>{escape(tr("header.suggested"))}</span><strong>{escape(tr("header.suggested_value", total=len(suggested_rows), high=high_count))}</strong></div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def count_high_or_critical(rows: list[MatrixRow]) -> int:
    return sum(1 for row in rows if row.nivel in {"high", "critical"})


def render_section_label(label: str) -> None:
    st.markdown(f'<div class="dtp-section-label">{escape(label)}</div>', unsafe_allow_html=True)


apply_dataprev_theme()


def context_state_key(context: ContractContext) -> str:
    return "|".join(
        [
            context.objeto,
            context.tipo_contratacao,
            str(context.valor_estimado),
            context.criticidade,
            context.prazo,
            context.modalidade,
            context.contexto,
        ]
    )


def ensure_suggestion_overrides(context: ContractContext) -> None:
    key = context_state_key(context)
    if st.session_state.get("suggestion_context_key") != key:
        st.session_state.suggestion_context_key = key
        st.session_state.force_include_ids = set()
        st.session_state.force_exclude_ids = set()


def split_suggestion_rows(
    base_suggested_rows: list[MatrixRow],
    all_library_rows: list[MatrixRow],
) -> tuple[list[MatrixRow], list[MatrixRow]]:
    base_ids = {row.id for row in base_suggested_rows}
    include_ids = set(st.session_state.get("force_include_ids", set()))
    exclude_ids = set(st.session_state.get("force_exclude_ids", set()))
    selected_ids = (base_ids | include_ids) - exclude_ids

    suggested = [row for row in all_library_rows if row.id in selected_ids]
    not_suggested = [row for row in all_library_rows if row.id not in selected_ids]
    return suggested, not_suggested


def suggestion_table_data(rows: list[MatrixRow]) -> list[dict[str, str]]:
    return [
        {
            tr("col.id"): row.id,
            tr("col.risk"): row.risco,
            tr("col.category"): category_label(row.categoria, LANG),
            tr("col.probability"): probability_label(row.probabilidade, LANG),
            tr("col.impact"): impact_label(row.impacto, LANG),
            tr("col.level"): risk_level_label(row.nivel, LANG),
        }
        for row in rows
    ]


def grouped_row_indexes(rows: list[MatrixRow]) -> list[tuple[str, list[tuple[int, MatrixRow]]]]:
    grouped: dict[str, list[tuple[int, MatrixRow]]] = defaultdict(list)
    for index, row in enumerate(rows):
        grouped[row.categoria or "planejamento"].append((index, row))

    def sort_key(item: tuple[str, list[tuple[int, MatrixRow]]]) -> tuple[int, str]:
        category = item[0]
        if category in CATEGORIES:
            return (CATEGORIES.index(category), category)
        return (len(CATEGORIES), category)

    return sorted(grouped.items(), key=sort_key)


def render_grouped_suggestion_tables(rows: list[MatrixRow], empty_message: str) -> None:
    if not rows:
        st.info(empty_message)
        return

    for category, indexed_rows in grouped_row_indexes(rows):
        category_rows = [row for _, row in indexed_rows]
        with st.expander(f"{category_label(category, LANG)} ({len(category_rows)})", expanded=True):
            st.dataframe(suggestion_table_data(category_rows), width="stretch", hide_index=True)


def row_option_label(row_lookup: dict[str, MatrixRow], risk_id: str) -> str:
    row = row_lookup[risk_id]
    return f"{row.id} - {row.risco}"


def move_risk_to_suggested(risk_id: str) -> None:
    st.session_state.force_include_ids.add(risk_id)
    st.session_state.force_exclude_ids.discard(risk_id)
    st.rerun()


def move_risk_to_not_suggested(risk_id: str) -> None:
    st.session_state.force_exclude_ids.add(risk_id)
    st.session_state.force_include_ids.discard(risk_id)
    st.rerun()


def render_suggestion_mover(
    rows: list[MatrixRow],
    select_label: str,
    button_label: str,
    key_prefix: str,
    on_move,
) -> None:
    if not rows:
        st.info(tr("empty.list"))
        return

    row_lookup = {row.id: row for row in rows}
    col1, col2 = st.columns([4, 1])
    with col1:
        selected_id = select(
            select_label,
            [row.id for row in rows],
            format_func=lambda risk_id: row_option_label(row_lookup, risk_id),
            key=f"{key_prefix}_select",
        )
    with col2:
        st.write("")
        st.write("")
        if st.button(button_label, key=f"{key_prefix}_button"):
            on_move(selected_id)


def render_language_selector() -> None:
    st.radio(
        tr("sidebar.language"),
        list(LANGUAGES),
        format_func=LANGUAGES.get,
        horizontal=True,
        key="lang",
    )
    st.query_params["lang"] = st.session_state.lang


def build_context() -> ContractContext:
    with st.sidebar:
        st.markdown(
            f"""
            <div class="dtp-sidebar-brand">
                <strong>Dataprev</strong>
                <span>{escape(tr("sidebar.brand"))}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_language_selector()
        st.header(tr("sidebar.contract"))
        objeto = st.text_area(tr("field.object"), value=tr("field.object_default"), key="ctx_objeto")
        tipo = select(
            tr("field.type"),
            CONTRACT_TYPES,
            format_func=label_in(contract_type_label),
            key="ctx_tipo",
        )
        valor = st.number_input(
            tr("field.value"),
            min_value=0.0,
            step=1000.0,
            help=tr("help.value"),
            key="ctx_valor",
        )
        criticidade = select(
            tr("field.criticality"),
            CRITICALITIES,
            index=1,
            format_func=label_in(criticality_label),
            help=tr("help.criticality"),
            key="ctx_criticidade",
        )
        prazo_meses = st.number_input(
            tr("field.term"),
            min_value=1,
            value=12,
            step=1,
            help=tr("help.term"),
            key="ctx_prazo",
        )
        modalidade = select(
            tr("field.modality"),
            MODALITIES,
            index=MODALITIES.index(DEFAULT_MODALITY),
            format_func=label_in(modality_label),
            help=tr("help.modality"),
            key="ctx_modalidade",
        )
        contexto = st.text_area(
            tr("field.context"),
            value=tr("field.context_default"),
            help=tr("help.context"),
            key="ctx_contexto",
        )
    return ContractContext(
        objeto=objeto,
        tipo_contratacao=tipo,
        valor_estimado=valor,
        criticidade=criticidade,
        # Mantido em PT: entra na chave de estado e no texto analisado pelas sugestoes.
        prazo=f"{prazo_meses} meses",
        modalidade=modalidade,
        contexto=contexto,
    )


FINAL_MATRIX_COLUMNS = {
    "id": "col.id",
    "risco": "col.risk",
    "categoria": "col.category",
    "causa": "col.cause",
    "consequencia": "col.consequence",
    "probabilidade": "col.probability",
    "impacto": "col.impact",
    "nivel": "col.level",
    "estrategia": "col.strategy",
    "acao_preventiva": "col.preventive",
    "acao_contingencia": "col.contingency",
    "justificativa": "col.rationale",
}


def final_matrix_table(rows: list[MatrixRow]) -> list[dict[str, str]]:
    table = []
    for row in rows:
        data = row_to_export_dict(row, LANG)
        table.append({tr(FINAL_MATRIX_COLUMNS[field]): data[field] for field in EXPORT_FIELDS})
    return table


def rows_to_xlsx(rows: list[MatrixRow]) -> bytes:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = t("export.sheet_title", DEFAULT_LANGUAGE)
    worksheet.append(EXPORT_FIELDS)
    for row in selected_rows(rows):
        data = row_to_export_dict(row)
        worksheet.append([data[field] for field in EXPORT_FIELDS])
    stream = io.BytesIO()
    workbook.save(stream)
    return stream.getvalue()


def ensure_manual_rows() -> None:
    if "manual_rows" not in st.session_state:
        st.session_state.manual_rows = []


def next_manual_id() -> str:
    ensure_manual_rows()
    return f"MAN{len(st.session_state.manual_rows) + 1:03d}"


def safe_index(options: list[str], value: str, default: int = 0) -> int:
    return options.index(value) if value in options else default


def add_manual_risk_form() -> None:
    ensure_manual_rows()
    with st.expander(tr("manual.expander"), expanded=False):
        with st.form("manual_risk_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                manual_id = st.text_input(tr("field.id"), value=next_manual_id())
                categoria = select(
                    tr("field.category"), CATEGORIES, format_func=label_in(category_label), key="manual_categoria"
                )
            with col2:
                probabilidade = select(
                    tr("field.probability"),
                    PROBABILITY_OPTIONS,
                    index=2,
                    format_func=label_in(probability_label),
                    key="manual_probabilidade",
                )
                impacto = select(
                    tr("field.impact"), IMPACT_OPTIONS, index=2, format_func=label_in(impact_label), key="manual_impacto"
                )
            with col3:
                estrategia = select(
                    tr("field.strategy"), STRATEGIES, format_func=label_in(strategy_label), key="manual_estrategia"
                )

            risco = st.text_input(tr("field.risk"))
            causa = st.text_area(tr("field.cause"))
            consequencia = st.text_area(tr("manual.consequence"))
            preventiva = st.text_area(tr("manual.preventive"))
            contingencia = st.text_area(tr("manual.contingency"))
            justificativa = st.text_area(tr("manual.notes"))
            submitted = st.form_submit_button(tr("manual.submit"))

        if submitted and risco.strip():
            st.session_state.manual_rows.append(
                MatrixRow(
                    id=manual_id.strip() or next_manual_id(),
                    risco=risco.strip(),
                    categoria=categoria,
                    causa=causa.strip(),
                    consequencias=[consequencia.strip()] if consequencia.strip() else [],
                    probabilidade=probabilidade,
                    impacto=impacto,
                    nivel=risk_level(probabilidade, impacto),
                    estrategia=estrategia,
                    acoes_preventivas=[ActionItem(preventiva.strip())] if preventiva.strip() else [],
                    acoes_contingencia=[ActionItem(contingencia.strip())] if contingencia.strip() else [],
                    justificativa=justificativa.strip() or tr("manual.default_note"),
                    tags=["manual"],
                )
            )
            st.success(tr("manual.added", id=manual_id))
        elif submitted:
            st.warning(tr("manual.missing_title"))


def edit_text_items(risk_key: str, slot: str, base_items: list[str]) -> list[str]:
    """``slot`` e fixo (compoe as chaves de estado); o rotulo vem de ``item.<slot>``."""
    label = tr(f"item.{slot}")
    count_key = f"{risk_key}_{slot}_count"
    deleted_key = f"{risk_key}_{slot}_deleted"
    if count_key not in st.session_state:
        st.session_state[count_key] = max(1, len(base_items))
    if deleted_key not in st.session_state:
        st.session_state[deleted_key] = []
    if st.button(tr("item.add", item=label.lower()), key=f"{risk_key}_{slot}_add"):
        st.session_state[count_key] += 1

    items: list[str] = []
    deleted = set(st.session_state[deleted_key])
    for index in range(st.session_state[count_key]):
        if index in deleted:
            continue
        default = base_items[index] if index < len(base_items) else ""
        col1, col2 = st.columns([5, 1])
        with col1:
            value = st.text_area(
                f"{label} {index + 1}",
                value=default,
                key=f"{risk_key}_{slot}_{index}",
            )
        with col2:
            st.write("")
            st.write("")
            if index > 0 and st.button(tr("item.delete"), key=f"{risk_key}_{slot}_delete_{index}"):
                st.session_state[deleted_key].append(index)
                st.rerun()
        if value.strip():
            items.append(value.strip())
    return items


def edit_action_items(risk_key: str, slot: str, base_actions: list[ActionItem]) -> list[ActionItem]:
    label = tr(f"item.{slot}")
    count_key = f"{risk_key}_{slot}_count"
    deleted_key = f"{risk_key}_{slot}_deleted"
    if count_key not in st.session_state:
        st.session_state[count_key] = max(1, len(base_actions))
    if deleted_key not in st.session_state:
        st.session_state[deleted_key] = []
    if st.button(tr("item.add", item=label.lower()), key=f"{risk_key}_{slot}_add"):
        st.session_state[count_key] += 1

    actions: list[ActionItem] = []
    deleted = set(st.session_state[deleted_key])
    for index in range(st.session_state[count_key]):
        if index in deleted:
            continue
        base = base_actions[index] if index < len(base_actions) else ActionItem("")
        col1, col2, col3, col4 = st.columns([3, 1, 2, 1])
        with col1:
            descricao = st.text_area(
                f"{label} {index + 1}",
                value=base.descricao,
                key=f"{risk_key}_{slot}_desc_{index}",
            )
        with col2:
            situacao = select(
                tr("field.status"),
                ACTION_STATUSES,
                index=safe_index(ACTION_STATUSES, base.situacao),
                format_func=label_in(action_status_label),
                key=f"{risk_key}_{slot}_sit_{index}",
            )
        with col3:
            responsavel = st.text_input(
                tr("field.owner"),
                value=base.responsavel,
                key=f"{risk_key}_{slot}_resp_{index}",
            )
        with col4:
            st.write("")
            st.write("")
            if index > 0 and st.button(tr("item.delete"), key=f"{risk_key}_{slot}_delete_{index}"):
                st.session_state[deleted_key].append(index)
                st.rerun()
        if descricao.strip():
            actions.append(ActionItem(descricao.strip(), situacao=situacao, responsavel=responsavel.strip()))
    return actions


def edit_rows(rows: list[MatrixRow], context: ContractContext) -> list[MatrixRow]:
    edited_by_index: dict[int, MatrixRow] = {}
    for category, indexed_rows in grouped_row_indexes(rows):
        render_section_label(f"{category_label(category, LANG)} ({len(indexed_rows)})")
        with st.container():
            for index, row in indexed_rows:
                risk_key = f"{row.id}_{index}"
                with st.expander(f"{row.id} - {row.risco}", expanded=row.selecionado):
                    selecionado = st.checkbox(tr("review.include"), value=row.selecionado, key=f"sel_{risk_key}")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        probabilidade = select(
                            tr("field.probability"),
                            PROBABILITY_OPTIONS,
                            index=PROBABILITY_OPTIONS.index(canonical_scale(row.probabilidade)),
                            format_func=label_in(probability_label),
                            key=f"prob_{risk_key}",
                        )
                    with col2:
                        impacto = select(
                            tr("field.impact"),
                            IMPACT_OPTIONS,
                            index=IMPACT_OPTIONS.index(canonical_scale(row.impacto)),
                            format_func=label_in(impact_label),
                            key=f"impacto_{risk_key}",
                        )
                    with col3:
                        nivel = risk_level(probabilidade, impacto)
                        st.metric(tr("field.level"), risk_level_label(nivel, LANG))

                    categoria = select(
                        tr("review.category"),
                        CATEGORIES,
                        index=safe_index(CATEGORIES, row.categoria),
                        format_func=label_in(category_label),
                        key=f"cat_{risk_key}",
                    )
                    estrategia = select(
                        tr("field.strategy"),
                        STRATEGIES,
                        index=safe_index(STRATEGIES, row.estrategia),
                        format_func=label_in(strategy_label),
                        key=f"estrategia_{risk_key}",
                    )

                    risco = st.text_input(tr("field.risk"), value=row.risco, key=f"risco_{risk_key}")
                    causa = st.text_area(tr("field.cause"), value=row.causa, key=f"causa_{risk_key}")
                    render_section_label(tr("section.consequences"))
                    consequencias = edit_text_items(risk_key, "consequence", row.consequencias)
                    render_section_label(tr("section.preventive"))
                    preventivas = edit_action_items(risk_key, "preventive", row.acoes_preventivas)
                    render_section_label(tr("section.contingency"))
                    contingencias = edit_action_items(risk_key, "contingency", row.acoes_contingencia)
                    justificativa = st.text_area(
                        tr("review.rationale"),
                        value=row.justificativa,
                        key=f"just_{risk_key}",
                    )
                    edited_row = MatrixRow(
                        id=row.id,
                        risco=risco,
                        categoria=categoria,
                        causa=causa,
                        consequencias=consequencias,
                        probabilidade=probabilidade,
                        impacto=impacto,
                        nivel=nivel,
                        estrategia=estrategia,
                        acoes_preventivas=preventivas,
                        acoes_contingencia=contingencias,
                        justificativa=justificativa,
                        selecionado=selecionado,
                        tags=row.tags,
                    )
                    if "manual" in row.tags:
                        if st.button(tr("review.save_library"), key=f"save_library_{risk_key}"):
                            result = save_matrix_row_to_library(DATA_PATH, edited_row, context)
                            if result.saved:
                                st.success(tr("library.saved", id=result.risk_id))
                                st.rerun()
                            elif result.risk_id:
                                st.info(tr("library.exists", id=result.risk_id))
                            else:
                                st.error(tr("library.error", detail=result.detail or result.message))
                    edited_by_index[index] = edited_row
    return [edited_by_index[index] for index in range(len(rows))]


context = build_context()
try:
    risks = load_risks(DATA_PATH)
except ValueError as exc:
    st.error(tr("error.load_library", detail=exc))
    st.stop()
base_suggested_rows = suggest_risks(risks, context)
all_library_rows = suggest_risks(risks, context, minimum_score=0, max_per_category=None)
ensure_suggestion_overrides(context)
suggested_rows, not_suggested_rows = split_suggestion_rows(base_suggested_rows, all_library_rows)

render_app_header(context, suggested_rows)

tab1, tab2, tab3 = st.tabs([tr("tab.suggestions"), tr("tab.review"), tr("tab.export")])

with tab1:
    render_panel_title(tr("panel.suggested"))
    col1, col2, col3 = st.columns(3)
    col1.metric(tr("metric.suggestions"), len(suggested_rows))
    col2.metric(tr("metric.high"), count_high_or_critical(suggested_rows))
    col3.metric(tr("metric.categories"), len({row.categoria for row in suggested_rows}))
    render_grouped_suggestion_tables(suggested_rows, tr("empty.suggested"))
    render_suggestion_mover(
        suggested_rows,
        tr("mover.select_suggested"),
        tr("mover.remove"),
        "remove_suggested",
        move_risk_to_not_suggested,
    )

    render_panel_title(tr("panel.not_included"))
    col1, col2, col3 = st.columns(3)
    col1.metric(tr("metric.available"), len(not_suggested_rows))
    col2.metric(tr("metric.high"), count_high_or_critical(not_suggested_rows))
    col3.metric(tr("metric.categories"), len({row.categoria for row in not_suggested_rows}))
    render_grouped_suggestion_tables(not_suggested_rows, tr("empty.not_included"))
    render_suggestion_mover(
        not_suggested_rows,
        tr("mover.select_not_included"),
        tr("mover.include"),
        "include_not_suggested",
        move_risk_to_suggested,
    )

with tab2:
    render_panel_title(tr("panel.review"))
    add_manual_risk_form()
    all_review_rows = [*suggested_rows, *st.session_state.manual_rows]
    edited_rows = edit_rows(all_review_rows, context)

with tab3:
    render_panel_title(tr("panel.final"))
    selected = selected_rows(edited_rows if "edited_rows" in locals() else suggested_rows)
    col1, col2, col3 = st.columns(3)
    col1.metric(tr("metric.selected"), len(selected))
    col2.metric(tr("metric.preventive"), sum(len(row.acoes_preventivas) for row in selected))
    col3.metric(tr("metric.contingency"), sum(len(row.acoes_contingencia) for row in selected))
    st.dataframe(final_matrix_table(selected), width="stretch", hide_index=True)
    if LANG != DEFAULT_LANGUAGE:
        st.caption(tr("export.pt_only"))

    csv_content = to_csv(selected)
    latex_content = to_latex(selected)
    docx_content = to_docx(selected, context)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.download_button(tr("download.csv"), csv_content, "matriz_riscos.csv", "text/csv")
    with col2:
        st.download_button(
            tr("download.excel"),
            rows_to_xlsx(selected),
            "matriz_riscos.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    with col3:
        st.download_button(tr("download.latex"), latex_content, "matriz_riscos.tex", "text/plain")
    with col4:
        st.download_button(
            tr("download.word"),
            docx_content,
            "mapa_de_gerenciamento_de_riscos.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
