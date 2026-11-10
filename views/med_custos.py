"""Custos sobre as dispensações."""

import streamlit as st

from charts import med_custos as graficos
from data.prepare_med import load_med, periodo_med
from views.common import exige
from views.sim_tema import cabecalho, secao


def render() -> None:
    """Página de custos (notebook Sprint 2)."""
    df = exige(load_med, "Nenhuma dispensação encontrada.")
    periodo = periodo_med(df)
    cabecalho(
        "O que os custos revelam sobre as dispensações?",
        f"Farmácia Básica · {periodo} · {len(df):,} registros · "
        f"R$ {df['custo_total'].sum():,.0f}".replace(",", "."),
        "medicamentos",
        total_descobertas=7,
    )
    secao("Evolução mensal", graficos.evolucao_mensal(df, periodo))
    secao("Medicamentos que mais custam", graficos.top_custo(df, periodo))
    secao(
        "Volume × custo",
        graficos.quantidade_vs_custo(df, periodo),
        graficos.boxplot_top5_custo(df, periodo),
    )
    secao(
        "Fabricantes e classes",
        graficos.top_fabricantes(df, periodo),
        graficos.top_classes(df, periodo),
    )
    secao(
        "Registros atípicos",
        (None, "Explore os valores que fogem do padrão nas tabelas."),
        extra=lambda: _tabelas_outliers(df),
    )


def _tabelas_outliers(df) -> None:
    """Abas de outliers acima da navegação."""
    abas = st.tabs(["Custo unitário", "Quantidade", "Custo do evento"])
    with abas[0]:
        st.dataframe(graficos.tabela_outliers(df, "unitario"), hide_index=True, width="stretch")
    with abas[1]:
        st.dataframe(graficos.tabela_outliers(df, "quantidade"), hide_index=True, width="stretch")
    with abas[2]:
        st.dataframe(graficos.tabela_outliers(df, "evento"), hide_index=True, width="stretch")
