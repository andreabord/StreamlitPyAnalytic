"""Gráficos: custos sobre as dispensações."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from charts.texto import historia_volume, vazio
from charts.theme import (
    PRIMARY,
    TERTIARY,
    abrevia,
    apply_layout,
    bar_horizontal,
    dispersao,
)


def evolucao_mensal(df: pd.DataFrame, periodo: str):
    """Barras de custo + linha de quantidade por mês."""
    mensal = (
        df.groupby("ano_mes")
        .agg(custo_total=("custo_total", "sum"), quantidade_total=("quantidade", "sum"))
        .reset_index()
        .sort_values("ano_mes")
    )
    if mensal.empty:
        return vazio()
    fig = go.Figure()
    fig.add_bar(
        x=mensal["ano_mes"],
        y=mensal["custo_total"] / 1e3,
        name="Custo (R$ mil)",
        marker_color=PRIMARY,
        opacity=0.75,
    )
    fig.add_scatter(
        x=mensal["ano_mes"],
        y=mensal["quantidade_total"] / 1e3,
        name="Qtd (mil un.)",
        mode="lines+markers",
        yaxis="y2",
        line=dict(color=TERTIARY, width=2),
    )
    fig.update_layout(
        yaxis=dict(title="Custo (R$ mil)"),
        yaxis2=dict(title="Quantidade (mil)", overlaying="y", side="right"),
    )
    fig = apply_layout(fig, f"Evolução mensal — custo e quantidade · {periodo}")
    fig.update_layout(
        legend=dict(orientation="h", yanchor="top", y=-0.22, xanchor="center", x=0.5),
        margin=dict(l=8, r=56, t=56, b=72),
        yaxis2=dict(title="Quantidade (mil)", overlaying="y", side="right"),
    )
    return fig, (
        f"No período {periodo} o custo total foi R$ {df['custo_total'].sum():,.0f} "
        f"em {len(df):,} dispensações. O gráfico compara custo e quantidade mês a mês."
    ).replace(",", ".")


def top_custo(df: pd.DataFrame, periodo: str):
    """Top 10 medicamentos por custo total."""
    serie = _agg_med(df).sort_values("custo_total", ascending=False).head(10)
    if serie.empty:
        return vazio()
    total = float(df["custo_total"].sum()) or 1.0
    plot = serie.set_index("material_nome_base")["custo_total"]
    plot.index = [abrevia(i, 40) for i in plot.index]
    fig = bar_horizontal(plot, f"Top 10 medicamentos por custo — {periodo}", mostrar_pct=False)
    lider = plot.index[0]
    pct = 100 * float(plot.iloc[0]) / total
    return fig, (
        f"No período {periodo}, \"{lider}\" concentra {pct:.1f}% do custo total "
        f"(R$ {float(plot.iloc[0]):,.0f}). Os 10 primeiros puxam boa parte do orçamento."
    ).replace(",", ".")


def tabela_outliers(df: pd.DataFrame, criterio: str) -> pd.DataFrame:
    """Top 10 registros atípicos por custo unitário, quantidade ou evento."""
    cols = {
        "unitario": (["data", "material_nome", "custo_medio", "quantidade", "custo_total", "fabricante_nome"], "custo_medio"),
        "quantidade": (["data", "material_nome", "quantidade", "custo_medio", "custo_total", "centro_custo_nome"], "quantidade"),
        "evento": (["data", "material_nome", "quantidade", "custo_medio", "custo_total", "fabricante_nome"], "custo_total"),
    }
    colunas, ordem = cols[criterio]
    tabela = df.sort_values(ordem, ascending=False).loc[:, colunas].head(10).copy()
    if "data" in tabela.columns:
        tabela["data"] = pd.to_datetime(tabela["data"]).dt.strftime("%d/%m/%Y")
    return tabela.reset_index(drop=True)

def quantidade_vs_custo(df: pd.DataFrame, periodo: str):
    """Dispersão quantidade × custo por medicamento."""
    base = _agg_med(df)
    if base.empty:
        return vazio()
    fig = dispersao(
        base["quantidade_total"] / 1e3,
        base["custo_total"] / 1e3,
        f"Quantidade × custo por medicamento — {periodo}",
        "Quantidade (mil un.)",
        "Custo (R$ mil)",
    )
    pearson = base["quantidade_total"].corr(base["custo_total"])
    spearman = base["quantidade_total"].rank().corr(base["custo_total"].rank())
    return (
        fig,
        f"Pearson r = {pearson:.2f} · Spearman ρ = {spearman:.2f} "
        "(próximo de 0 = volume e custo pouco ligados).",
    )


def boxplot_top5_custo(df: pd.DataFrame, periodo: str):
    """Distribuição da quantidade por saída nos 5 itens de maior custo."""
    from charts.theme import boxplot

    top5 = _agg_med(df).sort_values("custo_total", ascending=False).head(5)["material_nome_base"]
    grupos = {
        abrevia(str(nome), 22): df.loc[df["material_nome_base"] == nome, "quantidade"]
        for nome in top5
    }
    if not grupos:
        return vazio()
    fig = boxplot(grupos, f"Quantidade por saída — Top 5 em custo · {periodo}")
    return fig, (
        f"Entre os 5 itens de maior custo ({periodo}), a mediana e a dispersão da quantidade "
        f"por saída mostram protocolos mais ou menos regulares."
    )


def top_fabricantes(df: pd.DataFrame, periodo: str):
    """Top 5 fabricantes por custo."""
    bruto = df.groupby("fabricante_nome")["custo_total"].sum().sort_values(ascending=False)
    serie = bruto.head(5)
    if serie.empty:
        return vazio()
    fig = bar_horizontal(serie, f"Top 5 fabricantes por custo — {periodo}", mostrar_pct=False)
    return fig, historia_volume(int(bruto.sum()), periodo, serie, "reais de custo por fabricante")


def top_classes(df: pd.DataFrame, periodo: str):
    """Top 5 classes terapêuticas por custo."""
    bruto = (
        df.groupby("classe_terapeutica")["custo_total"].sum().sort_values(ascending=False)
    )
    serie = bruto.head(5)
    if serie.empty:
        return vazio()
    plot = serie.copy()
    plot.index = [abrevia(i, 40) for i in plot.index]
    fig = bar_horizontal(plot, f"Top 5 classes terapêuticas por custo — {periodo}", mostrar_pct=False)
    return fig, historia_volume(int(bruto.sum()), periodo, serie, "reais de custo por classe")


def _agg_med(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega custo e quantidade por medicamento base."""
    return (
        df.groupby("material_nome_base", as_index=False)
        .agg(custo_total=("custo_total", "sum"), quantidade_total=("quantidade", "sum"))
    )
