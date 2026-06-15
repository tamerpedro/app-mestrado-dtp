from __future__ import annotations

import base64
from html import escape
import io
from pathlib import Path

import streamlit as st
from openpyxl import Workbook

from src.docx_exporter import to_docx
from src.exporters import EXPORT_FIELDS, row_to_export_dict, selected_rows, to_csv, to_latex
from src.library_writer import save_matrix_row_to_library
from src.models import ActionItem, ContractContext, MatrixRow
from src.risk_library import load_risks
from src.scoring import IMPACT_OPTIONS, PROBABILITY_OPTIONS, canonical_impact, canonical_probability, risk_level
from src.suggestions import suggest_risks


DATA_PATH = Path("data/riscos_base.csv")
LOGO_PATH = Path("assets/dataprev-logo.png")
CATEGORY_OPTIONS = ["planejamento", "selecao", "gestao", "solucao", "instalacao", "cronograma"]
STRATEGY_OPTIONS = ["Mitigar", "Aceitar", "Compartilhar", "Evitar"]
SITUATION_OPTIONS = ["Não iniciado", "Iniciado", "Concluído"]


st.set_page_config(page_title="Matriz de Riscos TIC", layout="wide")


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
    high_count = sum(1 for row in suggested_rows if row.nivel in {"alto", "critico"})
    logo_uri = image_to_data_uri(LOGO_PATH)
    logo_html = (
        f'<div class="dtp-logo-wrap"><img src="{logo_uri}" alt="Logotipo Dataprev"></div>'
        if logo_uri
        else ""
    )
    st.markdown(
        f"""
        <section class="dtp-hero">
            <div class="dtp-hero-main">
                {logo_html}
                <div class="dtp-hero-copy">
                    <div class="dtp-kicker">Dataprev | Contratações de TIC</div>
                    <h1>Matriz de Riscos TIC</h1>
                    <p>Protótipo de apoio à elaboração, revisão e padronização do Mapa de Gerenciamento de Riscos.</p>
                </div>
            </div>
            <div class="dtp-status-grid">
                <div class="dtp-status"><span>Tipo</span><strong>{escape(context.tipo_contratacao.title())}</strong></div>
                <div class="dtp-status"><span>Criticidade</span><strong>{escape(context.criticidade.title())}</strong></div>
                <div class="dtp-status"><span>Riscos sugeridos</span><strong>{len(suggested_rows)} no total | {high_count} altos</strong></div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


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
            "id": row.id,
            "risco": row.risco,
            "categoria": row.categoria,
            "probabilidade": row.probabilidade,
            "impacto": row.impacto,
            "nivel": row.nivel,
        }
        for row in rows
    ]


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
        st.info("Nenhum risco nesta lista.")
        return

    row_lookup = {row.id: row for row in rows}
    col1, col2 = st.columns([4, 1])
    with col1:
        selected_id = st.selectbox(
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


def build_context() -> ContractContext:
    with st.sidebar:
        st.markdown(
            """
            <div class="dtp-sidebar-brand">
                <strong>Dataprev</strong>
                <span>Mapa de Riscos TIC</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.header("Contratação")
        objeto = st.text_area("Objeto", value="Contratação de solução de TIC")
        tipo = st.selectbox("Tipo", ["aquisicao", "servico", "software"])
        valor = st.number_input(
            "Valor estimado",
            min_value=0.0,
            step=1000.0,
            help="Registrado no contexto da contratação; pode apoiar regras futuras por faixa de valor.",
        )
        criticidade = st.selectbox(
            "Criticidade",
            ["baixa", "media", "alta"],
            index=1,
            help="Ajuda a priorizar sugestões de risco quando a criticidade é alta.",
        )
        prazo = st.text_input(
            "Prazo",
            value="12 meses",
            help="Entra no texto analisado para sugestões por prazo, entrega, implantação e cronograma.",
        )
        modalidade = st.text_input(
            "Modalidade",
            value="pregao eletronico",
            help="Entra no texto analisado para sugestões ligadas à seleção de fornecedor.",
        )
        contexto = st.text_area(
            "Contexto",
            value="Necessidade de padronizar a matriz de riscos da contratacao.",
            help="Campo livre usado para aproximar palavras-chave da biblioteca de riscos.",
        )
    return ContractContext(
        objeto=objeto,
        tipo_contratacao=tipo,
        valor_estimado=valor,
        criticidade=criticidade,
        prazo=prazo,
        modalidade=modalidade,
        contexto=contexto,
    )


def rows_to_xlsx(rows: list[MatrixRow]) -> bytes:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Matriz de Riscos"
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
    with st.expander("Adicionar risco manual", expanded=False):
        with st.form("manual_risk_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                manual_id = st.text_input("ID", value=next_manual_id())
                categoria = st.selectbox("Categoria", CATEGORY_OPTIONS)
            with col2:
                probabilidade = st.selectbox("Probabilidade", PROBABILITY_OPTIONS, index=2)
                impacto = st.selectbox("Impacto", IMPACT_OPTIONS, index=2)
            with col3:
                estrategia = st.selectbox("Estrategia", STRATEGY_OPTIONS)

            risco = st.text_input("Risco")
            causa = st.text_area("Causa")
            consequencia = st.text_area("Consequencia inicial")
            preventiva = st.text_area("Acao preventiva inicial")
            contingencia = st.text_area("Acao de contingencia inicial")
            justificativa = st.text_area("Observacoes / justificativa")
            submitted = st.form_submit_button("Adicionar risco")

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
                    justificativa=justificativa.strip() or "Inserido manualmente na revisão humana.",
                    tags=["manual"],
                )
            )
            st.success(f"Risco {manual_id} adicionado para revisao.")
        elif submitted:
            st.warning("Informe ao menos o titulo do risco para adicionar.")


def edit_text_items(risk_key: str, label: str, base_items: list[str]) -> list[str]:
    count_key = f"{risk_key}_{label}_count"
    deleted_key = f"{risk_key}_{label}_deleted"
    if count_key not in st.session_state:
        st.session_state[count_key] = max(1, len(base_items))
    if deleted_key not in st.session_state:
        st.session_state[deleted_key] = []
    if st.button(f"Adicionar {label.lower()}", key=f"{risk_key}_{label}_add"):
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
                key=f"{risk_key}_{label}_{index}",
            )
        with col2:
            st.write("")
            st.write("")
            if index > 0 and st.button("Excluir", key=f"{risk_key}_{label}_delete_{index}"):
                st.session_state[deleted_key].append(index)
                st.rerun()
        if value.strip():
            items.append(value.strip())
    return items


def edit_action_items(risk_key: str, label: str, base_actions: list[ActionItem]) -> list[ActionItem]:
    count_key = f"{risk_key}_{label}_count"
    deleted_key = f"{risk_key}_{label}_deleted"
    if count_key not in st.session_state:
        st.session_state[count_key] = max(1, len(base_actions))
    if deleted_key not in st.session_state:
        st.session_state[deleted_key] = []
    if st.button(f"Adicionar {label.lower()}", key=f"{risk_key}_{label}_add"):
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
                key=f"{risk_key}_{label}_desc_{index}",
            )
        with col2:
            situacao = st.selectbox(
                "Situacao",
                SITUATION_OPTIONS,
                index=safe_index(SITUATION_OPTIONS, base.situacao),
                key=f"{risk_key}_{label}_sit_{index}",
            )
        with col3:
            responsavel = st.text_input(
                "Responsavel pela acao",
                value=base.responsavel,
                key=f"{risk_key}_{label}_resp_{index}",
            )
        with col4:
            st.write("")
            st.write("")
            if index > 0 and st.button("Excluir", key=f"{risk_key}_{label}_delete_{index}"):
                st.session_state[deleted_key].append(index)
                st.rerun()
        if descricao.strip():
            actions.append(ActionItem(descricao.strip(), situacao=situacao, responsavel=responsavel.strip()))
    return actions


def edit_rows(rows: list[MatrixRow], context: ContractContext) -> list[MatrixRow]:
    edited: list[MatrixRow] = []
    for index, row in enumerate(rows):
        risk_key = f"{row.id}_{index}"
        with st.expander(f"{row.id} - {row.risco}", expanded=row.selecionado):
            selecionado = st.checkbox("Incluir na matriz", value=row.selecionado, key=f"sel_{risk_key}")
            col1, col2, col3 = st.columns(3)
            with col1:
                probabilidade = st.selectbox(
                    "Probabilidade",
                    PROBABILITY_OPTIONS,
                    index=PROBABILITY_OPTIONS.index(canonical_probability(row.probabilidade)),
                    key=f"prob_{risk_key}",
                )
            with col2:
                impacto = st.selectbox(
                    "Impacto",
                    IMPACT_OPTIONS,
                    index=IMPACT_OPTIONS.index(canonical_impact(row.impacto)),
                    key=f"impacto_{risk_key}",
                )
            with col3:
                nivel = risk_level(probabilidade, impacto)
                st.metric("Nivel", nivel)

            categoria = st.selectbox(
                "Categoria no mapa",
                CATEGORY_OPTIONS,
                index=safe_index(CATEGORY_OPTIONS, row.categoria),
                key=f"cat_{risk_key}",
            )
            estrategia = st.selectbox(
                "Estrategia",
                STRATEGY_OPTIONS,
                index=safe_index(STRATEGY_OPTIONS, row.estrategia),
                key=f"estrategia_{risk_key}",
            )

            risco = st.text_input("Risco", value=row.risco, key=f"risco_{risk_key}")
            causa = st.text_area("Causa", value=row.causa, key=f"causa_{risk_key}")
            render_section_label("Consequências")
            consequencias = edit_text_items(risk_key, "Consequencia", row.consequencias)
            render_section_label("Ações preventivas")
            preventivas = edit_action_items(risk_key, "Acao preventiva", row.acoes_preventivas)
            render_section_label("Ações de contingência")
            contingencias = edit_action_items(risk_key, "Acao de contingencia", row.acoes_contingencia)
            justificativa = st.text_area(
                "Justificativa da sugestao",
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
                if st.button("Salvar este risco na biblioteca", key=f"save_library_{risk_key}"):
                    result = save_matrix_row_to_library(DATA_PATH, edited_row, context)
                    if result.saved:
                        st.success(f"{result.message} ID: {result.risk_id}.")
                        st.rerun()
                    elif result.risk_id:
                        st.info(f"{result.message} ID existente: {result.risk_id}.")
                    else:
                        st.error(result.message)
            edited.append(edited_row)
    return edited


context = build_context()
try:
    risks = load_risks(DATA_PATH)
except ValueError as exc:
    st.error(f"Não foi possível carregar a biblioteca de riscos: {exc}")
    st.stop()
base_suggested_rows = suggest_risks(risks, context)
all_library_rows = suggest_risks(risks, context, minimum_score=0, max_per_category=None)
ensure_suggestion_overrides(context)
suggested_rows, not_suggested_rows = split_suggestion_rows(base_suggested_rows, all_library_rows)

render_app_header(context, suggested_rows)

tab1, tab2, tab3 = st.tabs(["Sugestões", "Revisão humana", "Exportação"])

with tab1:
    render_panel_title("Riscos sugeridos")
    col1, col2, col3 = st.columns(3)
    col1.metric("Sugestões", len(suggested_rows))
    col2.metric("Riscos altos", sum(1 for row in suggested_rows if row.nivel == "alto"))
    col3.metric("Categorias", len({row.categoria for row in suggested_rows}))
    st.dataframe(suggestion_table_data(suggested_rows), use_container_width=True, hide_index=True)
    render_suggestion_mover(
        suggested_rows,
        "Selecionar risco sugerido",
        "Remover",
        "remove_suggested",
        move_risk_to_not_suggested,
    )

    render_panel_title("Riscos não incluídos")
    col1, col2, col3 = st.columns(3)
    col1.metric("Disponíveis", len(not_suggested_rows))
    col2.metric("Riscos altos", sum(1 for row in not_suggested_rows if row.nivel == "alto"))
    col3.metric("Categorias", len({row.categoria for row in not_suggested_rows}))
    st.dataframe(suggestion_table_data(not_suggested_rows), use_container_width=True, hide_index=True)
    render_suggestion_mover(
        not_suggested_rows,
        "Selecionar risco não incluído",
        "Incluir",
        "include_not_suggested",
        move_risk_to_suggested,
    )

with tab2:
    render_panel_title("Revisão humana")
    add_manual_risk_form()
    all_review_rows = [*suggested_rows, *st.session_state.manual_rows]
    edited_rows = edit_rows(all_review_rows, context)

with tab3:
    render_panel_title("Matriz final")
    selected = selected_rows(edited_rows if "edited_rows" in locals() else suggested_rows)
    col1, col2, col3 = st.columns(3)
    col1.metric("Riscos selecionados", len(selected))
    col2.metric("Ações preventivas", sum(len(row.acoes_preventivas) for row in selected))
    col3.metric("Ações de contingência", sum(len(row.acoes_contingencia) for row in selected))
    st.dataframe([row_to_export_dict(row) for row in selected], use_container_width=True, hide_index=True)

    csv_content = to_csv(selected)
    latex_content = to_latex(selected)
    docx_content = to_docx(selected, context)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.download_button("Baixar CSV", csv_content, "matriz_riscos.csv", "text/csv")
    with col2:
        st.download_button(
            "Baixar Excel",
            rows_to_xlsx(selected),
            "matriz_riscos.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    with col3:
        st.download_button("Baixar LaTeX", latex_content, "matriz_riscos.tex", "text/plain")
    with col4:
        st.download_button(
            "Baixar Word",
            docx_content,
            "mapa_de_gerenciamento_de_riscos.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
