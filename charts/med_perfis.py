"""Gráficos: perfis de cuidado na farmácia básica (Card #16)."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from charts.texto import vazio
from charts.theme import bar_horizontal
from components.plot import plot


def volume_por_perfil(df: pd.DataFrame, periodo: str):
    """B1: Barras horizontais com percentagens e história alinhada aos dados."""
    serie = df["perfil_cuidado"].value_counts().sort_values(ascending=True)
    if serie.empty:
        return vazio()

    fig = bar_horizontal(serie, f"Medicamentos por perfil de cuidado — {periodo}", mostrar_pct=True)

    total = int(serie.sum())
    lider_nome = serie.index[-1]
    lider_qtd = int(serie.iloc[-1])
    lider_pct = 100 * lider_qtd / total
    segundo_nome = serie.index[-2]
    segundo_pct = 100 * serie.iloc[-2] / total
    terceiro_nome = serie.index[-3]
    terceiro_pct = 100 * serie.iloc[-3] / total

    insight = (
        f"Foram {total:,} dispensações de medicamentos (retiradas, e não pessoas). "
        f"{lider_nome} lidera ({lider_qtd:,}; {lider_pct:.1f}%), seguido de "
        f"{segundo_nome.lower()} ({segundo_pct:.1f}%) e {terceiro_nome.lower()} "
        f"({terceiro_pct:.1f}%): juntos, {lider_pct + segundo_pct + terceiro_pct:.1f}%."
    ).replace(",", ".")
    return fig, insight


def top5_por_perfil_seletor(df: pd.DataFrame, periodo: str) -> None:
    """B4: Seletor de perfil com Top 5 no padrão mobile de plot + história."""
    base = df.copy()
    base["med"] = base["material_nome"].fillna("").astype(str)
    tabela = (
        base.groupby(["perfil_cuidado", "med"])
        .size()
        .reset_index(name="saidas")
        .sort_values(["perfil_cuidado", "saidas"], ascending=[True, False])
        .groupby("perfil_cuidado", group_keys=False)
        .head(5)
    )
    tabela["med"] = tabela["med"].str.split("-").str[0].str.strip()

    perfis = sorted(tabela["perfil_cuidado"].unique())
    if not perfis:
        st.info("Sem dados de perfis disponíveis.")
        return

    perfil = st.selectbox("Escolha um grupo de cuidado:", perfis)
    sub = tabela[tabela["perfil_cuidado"] == perfil]
    serie = pd.Series(sub["saidas"].values, index=sub["med"].values).sort_values(ascending=True)
    fig = bar_horizontal(
        serie, f"Top 5 medicamentos em {perfil} — {periodo}", mostrar_pct=False
    )
    lider = serie.index[-1]
    n_lider = int(serie.iloc[-1])
    plot(
        fig,
        f'Top 5 em "{perfil}": "{lider}" lidera com {n_lider:,} saídas.'.replace(",", "."),
    )
