"""Gráficos de mortalidade evitável e desigualdades sociais."""

from __future__ import annotations

import pandas as pd

from charts.texto import (
    historia_cruzamento,
    historia_numerica,
    historia_proporcao,
    historia_volume,
    insight_top,
    n_br,
    vazio,
)
from charts.theme import (
    abrevia,
    bar_horizontal,
    bar_vertical,
    barras_agrupadas,
    barras_empilhadas,
    heatmap,
    histograma,
)
from data.constants import MAPA_ESC_CURTO, ORDEM_ESC, ORDEM_GRUPO_CAUSA, ROTULOS_FAIXAS_INFARTO


def raca_por_sexo(df: pd.DataFrame, periodo: str):
    """Óbitos por raça/cor e sexo."""
    base = df[~df["SEXO"].isin({"Ignorado"}) & ~df["RACACOR"].isin({"Ignorado"})]
    if base.empty:
        return vazio()
    tabela = pd.crosstab(base["RACACOR"], base["SEXO"])
    fig = barras_empilhadas(tabela, f"Óbitos por raça/cor e sexo — Araranguá, {periodo}")
    return fig, historia_cruzamento(tabela, "raça/cor", "sexo")


def distribuicao_idade(df: pd.DataFrame, periodo: str):
    """Histograma de idade ao óbito."""
    vals = df["IDADE_ANOS"].dropna()
    if vals.empty:
        return vazio("Sem idade preenchida.")
    fig = histograma(vals, f"Distribuição de óbitos por idade — Araranguá, {periodo}", nbins=20)
    return fig, (
        f"No período {periodo}, "
        + historia_numerica(vals, "óbitos com idade válida", "anos")
    )


def grupos_causa(df: pd.DataFrame, periodo: str):
    """Volume de óbitos por grupo CID-10."""
    serie = df["GRUPO_CAUSA"].value_counts()
    if serie.empty:
        return vazio()
    fig = bar_horizontal(serie, f"Óbitos por grupo de causas — Araranguá, {periodo}")
    return fig, historia_volume(len(df), periodo, serie, "óbitos")


def top_causas(df: pd.DataFrame, periodo: str):
    """Top 5 causas específicas (descrição CID)."""
    serie = df["CAUSABAS_DESC"].value_counts().head(5)
    if serie.empty:
        return vazio()
    serie.index = [abrevia(i, 45) for i in serie.index]
    fig = bar_horizontal(serie, f"Principais causas específicas — Araranguá, {periodo}")
    return fig, historia_volume(len(df), periodo, serie, "óbitos")


def heatmap_raca_esc(df: pd.DataFrame, periodo: str):
    """% do total: raça/cor × escolaridade."""
    base = df[(df["ESC2010"] != "Ignorado") & (df["RACACOR"] != "Ignorado")]
    if base.empty:
        return vazio("Sem raça e escolaridade preenchidas.")
    cont = pd.crosstab(base["RACACOR"], base["ESC2010"])
    tabela = cont.div(cont.values.sum()) * 100
    tabela = tabela.reindex(columns=[c for c in ORDEM_ESC if c in tabela.columns])
    tabela.columns = [MAPA_ESC_CURTO.get(c, c) for c in tabela.columns]
    tabela.index.name = "RACACOR"
    tabela.columns.name = "ESC2010"
    fig = heatmap(
        tabela.round(1),
        f"Raça/cor × escolaridade (% do total) — Araranguá, {periodo}",
    )
    return fig, historia_cruzamento(cont, "raça/cor", "escolaridade")


def heatmap_causa_esc(df: pd.DataFrame, periodo: str):
    """% dentro do grupo de causa × escolaridade."""
    base = df[df["ESC2010"] != "Ignorado"]
    if base.empty:
        return vazio("Sem escolaridade preenchida.")
    cont = pd.crosstab(base["GRUPO_CAUSA"], base["ESC2010"])
    tabela = cont.div(cont.sum(axis=1), axis=0) * 100
    tabela = tabela.reindex(columns=[c for c in ORDEM_ESC if c in tabela.columns])
    ordem = [g for g in ORDEM_GRUPO_CAUSA if g in tabela.index]
    tabela = tabela.reindex(ordem)
    tabela.columns = [MAPA_ESC_CURTO.get(c, c) for c in tabela.columns]
    tabela.index.name = "GRUPO_CAUSA"
    tabela.columns.name = "ESC2010"
    fig = heatmap(
        tabela.round(1),
        f"Grupo de causa × escolaridade (% na causa) — Araranguá, {periodo}",
        "YlGnBu",
    )
    return fig, historia_proporcao(
        tabela, f"No período {periodo}, cada grupo de causa soma 100% na escolaridade."
    )


def infarto_sexo(df: pd.DataFrame, periodo: str):
    """Óbitos por infarto segundo o sexo."""
    base = _infarto(df)
    if base.empty:
        return vazio("Sem óbitos por infarto no recorte.")
    serie = base["SEXO"].value_counts()
    fig = bar_vertical(serie, f"Infarto por sexo — Araranguá, {periodo}")
    return fig, historia_volume(len(base), periodo, serie, "óbitos por infarto")


def infarto_faixa(df: pd.DataFrame, periodo: str):
    """Óbitos por infarto segundo a faixa etária."""
    base = _infarto(df).dropna(subset=["FAIXA_INFARTO"])
    if base.empty:
        return vazio("Sem óbitos por infarto com idade.")
    serie = base["FAIXA_INFARTO"].value_counts().reindex(ROTULOS_FAIXAS_INFARTO, fill_value=0)
    fig = bar_vertical(serie, f"Infarto por faixa etária — Araranguá, {periodo}", mostrar_pct=False)
    return fig, historia_volume(len(base), periodo, serie, "óbitos por infarto")


def taxas_territorio(taxas: pd.DataFrame, periodo: str):
    """Taxas anuais por 100 mil: Araranguá × Criciúma × SC."""
    if taxas.empty:
        return vazio()
    ordem = [g for g in ORDEM_GRUPO_CAUSA if g in taxas.index]
    tabela = taxas.reindex(ordem).fillna(0)
    fig = barras_agrupadas(
        tabela,
        f"Média anual por 100 mil hab. — Ara × Criciúma × SC, {periodo}",
        horizontal=True,
    )
    # destaca o maior valor absoluto da tabela
    emp = tabela.stack()
    (grupo, lugar), valor = emp.idxmax(), float(emp.max())
    return fig, (
        f"Taxas médias anuais por 100 mil habitantes (Censo 2022), período {periodo}. "
        f'O maior valor é {valor:.1f}'.replace(".", ",")
        + f' em "{grupo}" ({lugar}).'
    )


def _infarto(df: pd.DataFrame) -> pd.DataFrame:
    """Filtra óbitos cuja causa básica é infarto (I21…)."""
    cid = df["CAUSABAS"].astype(str).str.upper()
    return df.loc[cid.str.startswith("I21", na=False)].copy()
