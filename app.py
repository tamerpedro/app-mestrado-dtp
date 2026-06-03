from __future__ import annotations

import io
from pathlib import Path

import streamlit as st
from openpyxl import Workbook

from src.docx_exporter import to_docx
from src.exporters import EXPORT_FIELDS, selected_rows, to_csv, to_latex
from src.models import ContractContext, MatrixRow
from src.risk_library import load_risks
from src.scoring import IMPACT_OPTIONS, PROBABILITY_OPTIONS, canonical_impact, canonical_probability, risk_level
from src.suggestions import suggest_risks


DATA_PATH = Path("data/riscos_base.csv")


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
        worksheet.append([getattr(row, field) for field in EXPORT_FIELDS])
    stream = io.BytesIO()
    workbook.save(stream)
    return stream.getvalue()


def edit_rows(rows: list[MatrixRow]) -> list[MatrixRow]:
    edited: list[MatrixRow] = []
    for row in rows:
        with st.expander(f"{row.id} - {row.risco}", expanded=row.selecionado):
            selecionado = st.checkbox("Incluir na matriz", value=row.selecionado, key=f"sel_{row.id}")
            col1, col2, col3 = st.columns(3)
            with col1:
                probabilidade = st.selectbox(
                    "Probabilidade",
                    PROBABILITY_OPTIONS,
                    index=PROBABILITY_OPTIONS.index(canonical_probability(row.probabilidade)),
                    key=f"prob_{row.id}",
                )
            with col2:
                impacto = st.selectbox(
                    "Impacto",
                    IMPACT_OPTIONS,
                    index=IMPACT_OPTIONS.index(canonical_impact(row.impacto)),
                    key=f"impacto_{row.id}",
                )
            with col3:
                nivel = risk_level(probabilidade, impacto)
                st.metric("Nivel", nivel)

            categoria = st.selectbox(
                "Categoria no mapa",
                ["planejamento", "selecao", "gestao", "solucao", "instalacao", "cronograma"],
                index=["planejamento", "selecao", "gestao", "solucao", "instalacao", "cronograma"].index(row.categoria),
                key=f"cat_{row.id}",
            )
            estrategia = st.selectbox(
                "Estrategia",
                ["Mitigar", "Aceitar", "Compartilhar", "Evitar"],
                index=["Mitigar", "Aceitar", "Compartilhar", "Evitar"].index(row.estrategia),
                key=f"estrategia_{row.id}",
            )

            risco = st.text_input("Risco", value=row.risco, key=f"risco_{row.id}")
            causa = st.text_area("Causa", value=row.causa, key=f"causa_{row.id}")
            consequencia = st.text_area(
                "Consequencia",
                value=row.consequencia,
                key=f"consequencia_{row.id}",
            )
            preventiva = st.text_area(
                "Acao preventiva",
                value=row.acao_preventiva,
                key=f"prev_{row.id}",
            )
            contingencia = st.text_area(
                "Acao de contingencia",
                value=row.acao_contingencia,
                key=f"cont_{row.id}",
            )
            responsavel = st.text_input(
                "Responsavel",
                value=row.responsavel,
                key=f"resp_{row.id}",
            )
            justificativa = st.text_area(
                "Justificativa da sugestao",
                value=row.justificativa,
                key=f"just_{row.id}",
            )
            edited.append(
                MatrixRow(
                    id=row.id,
                    risco=risco,
                    categoria=categoria,
                    causa=causa,
                    consequencia=consequencia,
                    probabilidade=probabilidade,
                    impacto=impacto,
                    nivel=nivel,
                    estrategia=estrategia,
                    acao_preventiva=preventiva,
                    acao_contingencia=contingencia,
                    responsavel=responsavel,
                    justificativa=justificativa,
                    selecionado=selecionado,
                    tags=row.tags,
                )
            )
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
    edited_rows = edit_rows(suggested_rows)

with tab3:
    st.subheader("Matriz final")
    selected = selected_rows(edited_rows if "edited_rows" in locals() else suggested_rows)
    st.dataframe([{field: getattr(row, field) for field in EXPORT_FIELDS} for row in selected], use_container_width=True)

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
