"""Cruzamentos (escolaridade x faixa, ocupações, sexo x local, causas x faixa)."""

from __future__ import annotations

import pandas as pd
import plotly.express as px

from charts.texto import historia_cruzamento, historia_proporcao, historia_volume, vazio
from charts.theme import abrevia, apply_layout, bar_horizontal, barras_empilhadas
from data.constants import MAPA_LOCAL_CURTO


def escolaridade_por_faixa(df: pd.DataFrame, periodo: str):
    """(Mantido caso necessário, mas removido da vista principal conforme A9)."""
    tabela = pd.crosstab(df["ESC2010"], df["FAIXA_ETARIA"])
    if tabela.empty:
        return vazio()
    fig = px.imshow(tabela, text_auto=True, color_continuous_scale="Reds")
    fig = apply_layout(fig, f"Escolaridade por faixa etária — Araranguá, {periodo}")
    return fig, historia_cruzamento(tabela, "escolaridade", "faixa etária")


def top_ocupacoes(df: pd.DataFrame, periodo: str):
    """A10: Principais ocupações agrupadas."""
    if "OCUPACAO_DESC" not in df.columns:
        return vazio("A coluna de ocupação não está disponível nesta base.")
    bruto = df["OCUPACAO_DESC"].value_counts()
    serie = bruto.head(10)
    if serie.empty:
        return vazio()
    rotulos = serie.rename(index=lambda c: abrevia(c, 40))
    fig = bar_horizontal(rotulos, f"Principais ocupações declaradas — Araranguá, {periodo}")
    return fig, historia_volume(int(bruto.sum()), periodo, serie, "óbitos com ocupação")


def sexo_por_local(df: pd.DataFrame, periodo: str):
    """A11: Sexo por local de ocorrência em barras empilhadas a 100%."""
    validos = df.loc[~df["SEXO"].isin({"Ignorado"}) & ~df["LOCOCOR"].isin({"Ignorado"})].copy()
    validos["LOCOCOR"] = validos["LOCOCOR"].map(MAPA_LOCAL_CURTO).fillna(validos["LOCOCOR"])
    tabela = pd.crosstab(validos["SEXO"], validos["LOCOCOR"], normalize="index") * 100
    fig = barras_empilhadas(
        tabela, f"Local de ocorrência por sexo (% a 100%) — Araranguá, {periodo}"
    )
    return fig, historia_proporcao(
        tabela,
        f"Entre {len(validos)} óbitos com sexo e local ({periodo}), cada sexo soma 100%.",
    )


def causas_por_faixa(df: pd.DataFrame, periodo: str):
    """A12: Causas básicas por faixa etária."""
    top_causas = df["CAUSABAS_DESC"].value_counts().head(5).index
    filtrado = df[df["CAUSABAS_DESC"].isin(top_causas)].copy()
    filtrado["CAUSABAS_DESC"] = filtrado["CAUSABAS_DESC"].apply(lambda c: abrevia(c, 35))
    tabela = pd.crosstab(filtrado["CAUSABAS_DESC"], filtrado["FAIXA_ETARIA"])
    if tabela.empty:
        return vazio()
    fig = px.imshow(
        tabela,
        text_auto=True,
        color_continuous_scale="Blues",
        aspect="auto",
    )
    fig = apply_layout(
        fig, f"Principais causas de óbito por faixa etária — Araranguá, {periodo}"
    )
    fig.update_layout(xaxis_title="Faixa etária", yaxis_title="Causa básica")
    return fig, historia_cruzamento(tabela, "causa", "faixa etária")
