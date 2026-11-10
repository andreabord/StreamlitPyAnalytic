"""Gráficos: dispensação por bairro e centro de custo (versão revisada)."""

from __future__ import annotations

import pandas as pd

from charts.texto import historia_cruzamento, historia_proporcao, historia_volume, n_br, vazio
from charts.theme import (
    MUTED,
    PRIMARY,
    abrevia,
    bar_horizontal,
    barras_agrupadas,
    barras_empilhadas,
    heatmap,
)
from data.prepare_med import MESES_S1, MESES_S2


def proporcao_cc(df: pd.DataFrame, periodo: str):
    """Quantidade por centro de custo (cinza = sem CC)."""
    serie = df.groupby("centro_custo_nome")["quantidade"].sum().sort_values(ascending=False)
    if serie.empty:
        return vazio()
    cores = [MUTED if i == "Sem Centro de Custo" else PRIMARY for i in serie.index]
    fig = bar_horizontal(
        serie, f"Quantidade por centro de custo — {periodo}", mostrar_pct=False, cores=cores
    )
    return fig, historia_volume(int(serie.sum()), periodo, serie, "unidades por centro de custo")


def top_bairros(df: pd.DataFrame, periodo: str):
    """Top 15 bairros por quantidade dispensada."""
    base = df.loc[~df["bairro_malformado"]]
    bruto = base.groupby("bairro_padronizado")["quantidade"].sum().sort_values(ascending=False)
    serie = bruto.head(15)
    if serie.empty:
        return vazio()
    fig = bar_horizontal(serie, f"Top 15 bairros por quantidade — {periodo}", mostrar_pct=False)
    return fig, historia_volume(int(bruto.sum()), periodo, serie, "unidades nos bairros")


def menores_bairros(df: pd.DataFrame, periodo: str):
    """Bairros com menor movimento (exclui malformados)."""
    base = df.loc[~df["bairro_malformado"]]
    bruto = base.groupby("bairro_padronizado")["quantidade"].sum().sort_values(ascending=True)
    serie = bruto.head(15)
    if serie.empty:
        return vazio()
    fig = bar_horizontal(serie, f"Bairros com menor movimento — {periodo}", mostrar_pct=False)
    menor = str(serie.index[0])
    maior = str(serie.index[-1])
    return fig, (
        f"No período {periodo}, o gráfico mostra os {len(serie)} bairros de menor movimento "
        f"(de {n_br(len(bruto))} com nome válido). "
        f'O menor é "{menor}" ({n_br(int(serie.iloc[0]))} un.) e, neste recorte, '
        f'o maior é "{maior}" ({n_br(int(serie.iloc[-1]))} un.).'
    )


def taxa_per_capita(df: pd.DataFrame, periodo: str):
    """Dispensação por mil habitantes (Censo 2022)."""
    from charts.texto import _num

    base = df.loc[df["no_censo"] & ~df["bairro_malformado"]]
    if base.empty:
        return vazio("Sem correspondência com o Censo IBGE para calcular a taxa.")
    agg = base.groupby(["chave_censo", "populacao_bairro"], as_index=False)["quantidade"].sum()
    agg["taxa"] = agg["quantidade"] / agg["populacao_bairro"] * 1000
    bruto = agg.set_index("chave_censo")["taxa"].sort_values(ascending=False)
    serie = bruto.head(20)
    fig = bar_horizontal(
        serie, f"Dispensação por mil hab. (Censo 2022) — {periodo}", mostrar_pct=False
    )
    lider = str(serie.index[0])
    return fig, (
        f"Taxa por mil habitantes (Censo 2022), período {periodo}. "
        f"O gráfico traz o top {len(serie)} de {n_br(len(bruto))} bairros mapeados. "
        f'Neste recorte, "{lider}" lidera com {_num(float(serie.iloc[0]))} un./mil hab.'
    )


def custo_por_cc(df: pd.DataFrame, periodo: str):
    """Custo total por centro de custo (sem o vazio)."""
    base = df.loc[df["centro_custo_nome"] != "Sem Centro de Custo"]
    serie = base.groupby("centro_custo_nome")["custo_total"].sum().sort_values(ascending=False)
    if serie.empty:
        return vazio()
    fig = bar_horizontal(serie, f"Custo total por centro de custo — {periodo}", mostrar_pct=False)
    return fig, historia_volume(int(serie.sum()), periodo, serie, "reais de custo")


def perfil_tipo_cc(df: pd.DataFrame, periodo: str):
    """% do tipo de tratamento por centro de custo."""
    base = df.loc[
        (df["centro_custo_nome"] != "Sem Centro de Custo") & df["tipo_tratamento"].notna()
    ]
    if base.empty:
        return vazio()
    tabela = (
        pd.crosstab(
            base["centro_custo_nome"],
            base["tipo_tratamento"],
            values=base["quantidade"],
            aggfunc="sum",
            normalize="index",
        )
        * 100
    )
    tabela = tabela[tabela.mean().sort_values(ascending=False).index]
    fig = barras_empilhadas(
        tabela, f"Perfil de tratamento por centro de custo (%) — {periodo}", horizontal=True
    )
    return fig, historia_proporcao(tabela, f"No período {periodo}, cada centro de custo soma 100% nos tipos de tratamento.")


def comparativo_semestres(df: pd.DataFrame, periodo: str):
    """Top 10 bairros: 5 meses vs 5 meses."""
    base = df.loc[df["ano_mes"].isin(MESES_S2 + MESES_S1) & ~df["bairro_malformado"]].copy()
    if base.empty:
        return vazio()
    base["periodo_5m"] = base["ano_mes"].map(
        lambda m: "S2/2025 (5m)" if m in MESES_S2 else "S1/2026 (5m)"
    )
    top10 = (
        base.groupby("bairro_padronizado")["quantidade"].sum().sort_values(ascending=False).head(10).index
    )
    tabela = (
        base.loc[base["bairro_padronizado"].isin(top10)]
        .groupby(["bairro_padronizado", "periodo_5m"])["quantidade"]
        .sum()
        .unstack(fill_value=0)
    )
    ordem = tabela.sum(axis=1).sort_values(ascending=False).index
    tabela = tabela.reindex(ordem)
    fig = barras_agrupadas(tabela, f"Top 10 bairros — semestres comparáveis · {periodo}")
    s1 = tabela.filter(like="S1").sum().sum() if any("S1" in c for c in tabela.columns) else 0
    s2 = tabela.filter(like="S2").sum().sum() if any("S2" in c for c in tabela.columns) else 0
    return fig, (
        f"Comparação justa de 5 meses em cada semestre, período {periodo}. "
        f"No top 10 bairros, S2/2025 soma {int(s2):,} unidades e S1/2026 soma {int(s1):,}."
        .replace(",", ".")
    )


def comparativo_semestres_cc(df: pd.DataFrame, periodo: str):
    """Centros de custo: 5 meses vs 5 meses."""
    base = df.loc[
        df["ano_mes"].isin(MESES_S2 + MESES_S1)
        & (df["centro_custo_nome"] != "Sem Centro de Custo")
    ].copy()
    if base.empty:
        return vazio()
    base["periodo_5m"] = base["ano_mes"].map(
        lambda m: "S2/2025 (5m)" if m in MESES_S2 else "S1/2026 (5m)"
    )
    top = (
        base.groupby("centro_custo_nome")["quantidade"]
        .sum()
        .sort_values(ascending=False)
        .head(8)
        .index
    )
    tabela = (
        base.loc[base["centro_custo_nome"].isin(top)]
        .groupby(["centro_custo_nome", "periodo_5m"])["quantidade"]
        .sum()
        .unstack(fill_value=0)
    )
    tabela = tabela.reindex(tabela.sum(axis=1).sort_values(ascending=False).index)
    fig = barras_agrupadas(tabela, f"Centros de custo — semestres comparáveis · {periodo}")
    return fig, (
        f"Mesma janela de 5 meses por semestre nos centros de custo ({periodo}). "
        + historia_volume(
            int(tabela.values.sum()),
            periodo,
            tabela.sum(axis=1),
            "unidades nos centros",
        )
    )


def heatmap_bairro_tipo(df: pd.DataFrame, periodo: str):
    """Heatmap tipo de tratamento × top 30 bairros (%)."""
    base = df.loc[df["tipo_tratamento"].notna() & ~df["bairro_malformado"]]
    contagem = base.groupby("bairro_padronizado").size()
    validos = contagem[contagem >= 50].index
    top = (
        base.loc[base["bairro_padronizado"].isin(validos)]
        .groupby("bairro_padronizado")["quantidade"]
        .sum()
        .sort_values(ascending=False)
        .head(30)
        .index
    )
    recorte = base.loc[base["bairro_padronizado"].isin(top)]
    if recorte.empty:
        return vazio()
    tabela = (
        pd.crosstab(
            recorte["bairro_padronizado"],
            recorte["tipo_tratamento"],
            values=recorte["quantidade"],
            aggfunc="sum",
            normalize="index",
        )
        * 100
    )
    tabela.columns = [abrevia(c, 18) for c in tabela.columns]
    tabela.index.name = "bairro"
    tabela.columns.name = "tipo_tratamento"
    fig = heatmap(
        tabela.round(0),
        f"Tipo de tratamento × bairro (% no bairro) — Top 30 · {periodo}",
        "YlGnBu",
        cor_legenda="% no bairro",
    )
    cont = pd.crosstab(
        recorte["bairro_padronizado"],
        recorte["tipo_tratamento"],
        values=recorte["quantidade"],
        aggfunc="sum",
    ).fillna(0)
    return fig, historia_cruzamento(cont, "bairro", "tipo de tratamento")
