"""Gráficos: medicamentos em destaque na dispensação."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from charts.texto import historia_volume, n_br, vazio
from charts.theme import PALETTE, abrevia, apply_layout, bar_horizontal, dispersao, heatmap
from data.prepare_med import meses_completos

_CLASSES_SAZON = (
    "Antibióticos e antimicrobianos",
    "Analgésicos e antitérmicos",
    "Sistema respiratório",
    "Saúde mental e neurologia",
    "Doenças cardiovasculares",
)


def top_saidas(df: pd.DataFrame, periodo: str):
    """Top 10 medicamentos mais dispensados, com história alinhada aos dados."""
    bruto = df["material_nome_base"].value_counts().head(10)
    if bruto.empty:
        return vazio()
    total = int(df["material_nome_base"].value_counts().sum())
    lider, segundo, terceiro = bruto.index[0], bruto.index[1], bruto.index[2]
    n1, n2, n3 = int(bruto.iloc[0]), int(bruto.iloc[1]), int(bruto.iloc[2])
    pct_lider = 100 * n1 / total if total else 0
    pct_top = 100 * bruto.sum() / total if total else 0
    serie = bruto.copy()
    serie.index = [abrevia(i, 40) for i in serie.index]
    fig = bar_horizontal(
        serie, f"Top 10 medicamentos mais dispensados — {periodo}", mostrar_pct=False
    )
    insight = (
        f"O {lider.lower()} foi o mais dispensado ({n1:,}; {pct_lider:.1f}% do total), "
        f"seguido do {segundo.lower()} ({n2:,}) e da {terceiro.lower()} ({n3:,}). "
        f"Os 10 primeiros juntos somam {pct_top:.1f}% das dispensações."
    ).replace(",", ".")
    return fig, insight


def top_quantidade(df: pd.DataFrame, periodo: str):
    """Top 20 medicamentos por quantidade total."""
    bruto = df.groupby("material_nome_base")["quantidade"].sum().sort_values(ascending=False)
    serie = bruto.head(20)
    if serie.empty:
        return vazio()
    plot = serie.copy()
    plot.index = [abrevia(i, 40) for i in plot.index]
    fig = bar_horizontal(
        plot, f"Top 20 medicamentos por quantidade — {periodo}", mostrar_pct=False
    )
    return fig, historia_volume(int(bruto.sum()), periodo, serie, "unidades dispensadas")


def comparacao_rankings(df: pd.DataFrame, periodo: str):
    """Dispersão: ranking de saídas × ranking de quantidade (top 20 por saídas)."""
    saidas = df["material_nome_base"].value_counts().rename("saidas")
    qtd = df.groupby("material_nome_base")["quantidade"].sum().rename("quantidade")
    base = (
        pd.concat([saidas, qtd], axis=1)
        .dropna()
        .assign(
            rank_saidas=lambda d: d["saidas"].rank(ascending=False, method="min"),
            rank_quantidade=lambda d: d["quantidade"].rank(ascending=False, method="min"),
        )
        .sort_values("rank_saidas")
        .head(20)
    )
    if base.empty:
        return vazio()
    fig = dispersao(
        base["rank_saidas"],
        base["rank_quantidade"],
        f"Ranking saídas × quantidade (top 20 saídas) — {periodo}",
        "Posição em saídas (1 = mais)",
        "Posição em quantidade (1 = mais)",
    )
    return fig, (
        f"No período {periodo}, cada ponto é um medicamento do top 20 em saídas. "
        "Pontos longe da diagonal saem muito em pouca quantidade ou o contrário."
    )


def evolucao_top5(df: pd.DataFrame, periodo: str):
    """Linhas mensais dos 5 medicamentos com mais saídas."""
    base = meses_completos(df)
    top5 = base["material_nome_base"].value_counts().head(5).index
    evolucao = (
        base.loc[base["material_nome_base"].isin(top5)]
        .groupby(["ano_mes", "material_nome_base"])
        .size()
        .reset_index(name="saidas")
    )
    if evolucao.empty:
        return vazio()
    fig = go.Figure()
    for i, med in enumerate(top5):
        dados = evolucao.loc[evolucao["material_nome_base"] == med].sort_values("ano_mes")
        fig.add_scatter(
            x=dados["ano_mes"],
            y=dados["saidas"],
            mode="lines+markers",
            name=abrevia(str(med), 28),
            line=dict(color=PALETTE[i % len(PALETTE)]),
        )
    fig = apply_layout(fig, f"Evolução mensal — Top 5 medicamentos · {periodo}")
    nomes = ", ".join(f'"{abrevia(str(m), 28)}"' for m in top5)
    return fig, (
        f"No período {periodo}, o gráfico acompanha os 5 medicamentos com mais saídas: "
        f"{nomes}."
    )


def tipos_tratamento(df: pd.DataFrame, periodo: str):
    """Volume por tipo de tratamento."""
    bruto = df["tipo_tratamento"].fillna("Não informado").value_counts()
    serie = bruto.head(12)
    if serie.empty:
        return vazio()
    plot = serie.copy()
    plot.index = [abrevia(i, 40) for i in plot.index]
    fig = bar_horizontal(plot, f"Tipos de tratamento — {periodo}")
    return fig, historia_volume(int(bruto.sum()), periodo, serie, "saídas por tipo de tratamento")


def tipos_apresentacao(df: pd.DataFrame, periodo: str):
    """Tipos de apresentação (comprimido, frasco etc.)."""
    if "material_tipo" not in df.columns:
        return vazio("Sem coluna de tipo de apresentação.")
    bruto = df["material_tipo"].fillna("Não informado").value_counts()
    serie = bruto.head(15)
    if serie.empty:
        return vazio()
    plot = serie.copy()
    plot.index = [abrevia(i, 40) for i in plot.index]
    fig = bar_horizontal(plot, f"Tipos de apresentação — {periodo}", mostrar_pct=False)
    return fig, historia_volume(int(bruto.sum()), periodo, serie, "saídas por apresentação")


def top_apresentacoes(df: pd.DataFrame, periodo: str):
    """Top 20 apresentações completas (nome + dose + tipo)."""
    bruto = df["apresentacao_completa"].value_counts()
    serie = bruto.head(20)
    if serie.empty:
        return vazio()
    plot = serie.copy()
    plot.index = [abrevia(i, 48) for i in plot.index]
    fig = bar_horizontal(plot, f"Top 20 apresentações completas — {periodo}", mostrar_pct=False)
    return fig, historia_volume(int(bruto.sum()), periodo, serie, "saídas por apresentação completa")


def top_bairros_saidas(df: pd.DataFrame, periodo: str):
    """Top 15 bairros por número de saídas."""
    base = df.loc[~df["bairro_malformado"]]
    bruto = base["bairro_padronizado"].value_counts()
    serie = bruto.head(15)
    if serie.empty:
        return vazio()
    fig = bar_horizontal(serie, f"Top 15 bairros por saídas — {periodo}", mostrar_pct=False)
    return fig, historia_volume(int(bruto.sum()), periodo, serie, "saídas por bairro")


def media_quantidade(df: pd.DataFrame, periodo: str):
    """Média de quantidade por saída — universo = top 20 por saídas."""
    from charts.texto import _num

    top20 = df["material_nome_base"].value_counts().head(20).index
    media = (
        df.loc[df["material_nome_base"].isin(top20)]
        .groupby("material_nome_base")["quantidade"]
        .mean()
        .sort_values(ascending=False)
        .round(1)
    )
    if media.empty:
        return vazio()
    plot = media.copy()
    plot.index = [abrevia(i, 40) for i in plot.index]
    fig = bar_horizontal(
        plot, f"Média de quantidade por saída — Top 20 por saídas · {periodo}", mostrar_pct=False
    )
    lider = str(media.index[0])
    return fig, (
        f"Entre os 20 medicamentos com mais saídas ({periodo}), "
        f'"{lider}" tem a maior média por saída ({_num(float(media.iloc[0]))} un.). '
        f"A menor média neste recorte é {_num(float(media.iloc[-1]))} un."
    )


def top_meds_por_bairro(df: pd.DataFrame, periodo: str):
    """Heatmap: top 5 medicamentos nos 10 bairros com mais saídas."""
    base = df.loc[~df["bairro_malformado"]]
    bairros = base["bairro_padronizado"].value_counts().head(10).index
    recorte = base.loc[base["bairro_padronizado"].isin(bairros)]
    if recorte.empty:
        return vazio()
    ranking = (
        recorte.groupby(["bairro_padronizado", "material_nome_base"])
        .size()
        .reset_index(name="saidas")
        .sort_values(["bairro_padronizado", "saidas"], ascending=[True, False])
        .groupby("bairro_padronizado", group_keys=False)
        .head(5)
    )
    pivot = ranking.pivot_table(
        index="bairro_padronizado",
        columns="material_nome_base",
        values="saidas",
        fill_value=0,
    )
    pivot = pivot.loc[:, (pivot > 0).any()]
    pivot.columns = [abrevia(c, 18) for c in pivot.columns]
    pivot.index.name = "bairro"
    pivot.columns.name = "medicamento"
    fig = heatmap(
        pivot,
        f"Top medicamentos por bairro (saídas) — {periodo}",
        "YlGnBu",
        cor_legenda="Saídas",
    )
    return fig, (
        f"No período {periodo}, cada bairro exibe apenas seus 5 medicamentos líderes em saídas. "
        "Células zeradas estão fora do top local."
    )


def sazonalidade_tipo(df: pd.DataFrame, periodo: str):
    """Evolução mensal dos principais tipos de tratamento (texto da auditoria)."""
    base = meses_completos(df).dropna(subset=["tipo_tratamento"])
    if base.empty:
        return vazio("Sem tipo de tratamento preenchido.")

    pivot = (
        base.groupby(["ano_mes", "tipo_tratamento"])
        .size()
        .unstack(fill_value=0)
        .sort_index()
    )
    top_perfis = base["tipo_tratamento"].value_counts().head(3).index.tolist()
    pivot_top = pivot[[c for c in top_perfis if c in pivot.columns]]

    fig = go.Figure()
    for i, col in enumerate(pivot_top.columns):
        fig.add_scatter(
            x=pivot_top.index.astype(str),
            y=pivot_top[col],
            mode="lines+markers",
            name=abrevia(str(col), 28),
            line=dict(color=PALETTE[i % len(PALETTE)], width=1.8),
            marker=dict(size=5),
        )
    fig = apply_layout(fig, f"Evolução mensal dos principais perfis — {periodo}")
    if not top_perfis or pivot_top.empty:
        return fig, f"Evolução mensal dos principais tipos de tratamento ({periodo})."
    lider = top_perfis[0]
    nomes = ", ".join(f'"{abrevia(str(c), 28)}"' for c in pivot_top.columns)
    if lider in pivot_top.columns:
        serie_lider = pivot_top[lider]
        return fig, (
            f"No período {periodo}, o gráfico mostra {len(pivot_top.columns)} perfis: {nomes}. "
            f'"{abrevia(lider, 28)}" vai de {n_br(int(serie_lider.min()))} a '
            f"{n_br(int(serie_lider.max()))} dispensações no mês."
        )
    return fig, (
        f"No período {periodo}, o gráfico mostra {len(pivot_top.columns)} perfis: {nomes}."
    )
