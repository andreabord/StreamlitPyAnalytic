"""Gráficos: lotes e prazos de validade."""

from __future__ import annotations

import pandas as pd

from charts.theme import PRIMARY, apply_layout, bar_horizontal, histograma
from charts.texto import historia_volume, n_br, vazio
from charts.vac_common import com_data


def diversidade_lotes_vacina(df: pd.DataFrame, periodo: str, n: int = 12):
    """Quantidade de lotes distintos por vacina."""
    base = com_data(df).dropna(subset=["lote"])
    bruto = base.groupby("nome_da_vacina")["lote"].nunique().sort_values(ascending=False)
    serie = bruto.head(n)
    if serie.empty:
        return vazio()
    fig = bar_horizontal(serie, f"Diversidade de lotes por vacina — {periodo}", mostrar_pct=False)
    fig.update_xaxes(title="Lotes distintos")
    return fig, _historia_diversidade(serie, periodo, "vacina", len(bruto))


def diversidade_lotes_bairro(df: pd.DataFrame, periodo: str, n: int = 12):
    """Quantidade de lotes distintos por bairro da pessoa vacinada."""
    base = com_data(df).dropna(subset=["lote"])
    bruto = base.groupby("bairro")["lote"].nunique().sort_values(ascending=False)
    serie = bruto.head(n)
    if serie.empty:
        return vazio()
    fig = bar_horizontal(serie, f"Diversidade de lotes por bairro — {periodo}", mostrar_pct=False)
    fig.update_xaxes(title="Lotes distintos")
    return fig, _historia_diversidade(serie, periodo, "bairro", len(bruto))


def prazo_restante(df: pd.DataFrame, periodo: str):
    """Distribuição do prazo restante (dias) na data da aplicação."""
    base = com_data(df).dropna(subset=["prazo_restante_dias"])
    # remove negativos extremos / absurdos
    vals = base.loc[base["prazo_restante_dias"].between(0, 2000), "prazo_restante_dias"]
    if vals.empty:
        return vazio()
    fig = histograma(vals, f"Prazo restante do lote na aplicação (dias) — {periodo}", nbins=30)
    fig.update_xaxes(title="Dias até a validade")
    fig.update_yaxes(title="Número de aplicações")
    med = float(vals.median())
    return apply_layout(fig, fig.layout.title.text), (
        f"Há {n_br(len(vals))} aplicações com validade no período {periodo}. "
        f"A mediana do prazo restante na aplicação é {med:.0f} dias "
        f"(de {vals.min():.0f} a {vals.max():.0f})."
    )


def lotes_mais_usados(df: pd.DataFrame, periodo: str, n: int = 10):
    """Lotes com mais aplicações (código do lote)."""
    base = com_data(df).dropna(subset=["lote"])
    bruto = base["lote"].value_counts()
    serie = bruto.head(n)
    if serie.empty:
        return vazio()
    fig = bar_horizontal(serie, f"Lotes com mais aplicações — {periodo}")
    fig.update_xaxes(title="Número de aplicações")
    return fig, historia_volume(int(bruto.sum()), periodo, serie, "aplicações com lote")


def _historia_diversidade(serie, periodo: str, eixo: str, n_total: int) -> str:
    """Texto de ranking de lotes distintos (não é volume de aplicações)."""
    lider = str(serie.index[0])
    n1 = int(serie.iloc[0])
    return (
        f"No período {periodo}, o gráfico mostra o top {len(serie)} de {n_br(n_total)} "
        f"{eixo}s com lote informado. "
        f'"{lider}" lidera com {n_br(n1)} lotes distintos.'
    )
