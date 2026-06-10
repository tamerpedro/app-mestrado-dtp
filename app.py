from __future__ import annotations

import io
from pathlib import Path

import streamlit as st
from openpyxl import Workbook

from src.docx_exporter import to_docx
from src.exporters import EXPORT_FIELDS, row_to_export_dict, selected_rows, to_csv, to_latex
from src.models import ActionItem, ContractContext, MatrixRow
from src.risk_library import load_risks, save_matrix_row_to_library
from src.scoring import IMPACT_OPTIONS, PROBABILITY_OPTIONS, canonical_impact, canonical_probability, risk_level
from src.suggestions import suggest_risks


DATA_PATH = Path("data/riscos_base.csv")
CATEGORY_OPTIONS = ["planejamento", "selecao", "gestao", "solucao", "instalacao", "cronograma"]
STRATEGY_OPTIONS = ["Mitigar", "Aceitar", "Compartilhar", "Evitar"]
SITUATION_OPTIONS = ["Não iniciado", "Iniciado", "Concluído"]


st.set_page_config(page_title="Matriz de Riscos TIC", layout="wide")


def build_context() -> ContractContext:
    with st.sidebar:
        st.header("Contratacao")
        objeto = st.text_area("Objeto", value="Contratacao de solucao de TIC")
        tipo = st.selectbox("Tipo", ["aquisicao", "servico", "software"])
        area = st.text_input("Area demandante", value="Area demandante")
        valor = st.number_input("Valor estimado", min_value=0.0, step=1000.0)
        criticidade = st.selectbox("Criticidade", ["baixa", "media", "alta"], index=1)
        prazo = st.text_input("Prazo", value="12 meses")
        modalidade = st.text_input("Modalidade", value="pregao eletronico")
        contexto = st.text_area(
            "Contexto",
            value="Necessidade de padronizar a matriz de riscos da contratacao.",
        )
    return ContractContext(
        objeto=objeto,
        tipo_contratacao=tipo,
        area_demandante=area,
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
                responsavel = st.text_input("Responsavel", value="Equipe de planejamento")

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
                    acoes_preventivas=[
                        ActionItem(preventiva.strip(), responsavel=responsavel.strip())
                    ]
                    if preventiva.strip()
                    else [],
                    acoes_contingencia=[
                        ActionItem(contingencia.strip(), responsavel=responsavel.strip())
                    ]
                    if contingencia.strip()
                    else [],
                    responsavel=responsavel.strip(),
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


def edit_action_items(risk_key: str, label: str, base_actions: list[ActionItem], default_owner: str) -> list[ActionItem]:
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
        base = base_actions[index] if index < len(base_actions) else ActionItem("", responsavel=default_owner)
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
                value=base.responsavel or default_owner,
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
            responsavel = st.text_input(
                "Responsavel padrao",
                value=row.responsavel,
                key=f"resp_{risk_key}",
            )
            consequencias = edit_text_items(risk_key, "Consequencia", row.consequencias)
            preventivas = edit_action_items(risk_key, "Acao preventiva", row.acoes_preventivas, responsavel)
            contingencias = edit_action_items(risk_key, "Acao de contingencia", row.acoes_contingencia, responsavel)
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
                responsavel=responsavel,
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


st.title("Matriz de Riscos TIC")

context = build_context()
risks = load_risks(DATA_PATH)
suggested_rows = suggest_risks(risks, context)

tab1, tab2, tab3 = st.tabs(["Sugestoes", "Revisao", "Exportacao"])

with tab1:
    st.subheader("Riscos sugeridos")
    st.dataframe(
        [
            {
                "id": row.id,
                "risco": row.risco,
                "categoria": row.categoria,
                "probabilidade": row.probabilidade,
                "impacto": row.impacto,
                "nivel": row.nivel,
                "responsavel": row.responsavel,
            }
            for row in suggested_rows
        ],
        use_container_width=True,
    )

with tab2:
    st.subheader("Revisao humana")
    add_manual_risk_form()
    all_review_rows = [*suggested_rows, *st.session_state.manual_rows]
    edited_rows = edit_rows(all_review_rows, context)

with tab3:
    st.subheader("Matriz final")
    selected = selected_rows(edited_rows if "edited_rows" in locals() else suggested_rows)
    st.dataframe([row_to_export_dict(row) for row in selected], use_container_width=True)

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
