"""Gráficos territoriais: ranking SC e município de ocorrência."""

from __future__ import annotations

import pandas as pd

from charts.theme import PRIMARY, TERTIARY, bar_horizontal
from data.ranking import nome_ararangua, posicao, serie_absoluta, serie_taxa


def ranking_absoluto(ano_min: int, ano_max: int, periodo: str):
    """Top 15 municípios de SC por número de óbitos."""
    ranking = serie_absoluta(ano_min, ano_max)
    top = ranking.head(15)
    if top.empty:
        return None, "Sem dados para o ranking estadual.", ranking
    nome = nome_ararangua()
    cores = [TERTIARY if m == nome else PRIMARY for m in top.index]
    fig = bar_horizontal(
        top, f"Top 15 municípios de SC por óbitos — {periodo}", False, cores
    )
    return fig, _insight_top_n(ranking, top, nome, "óbitos"), ranking


def ranking_taxa(ano_min: int, ano_max: int, periodo: str):
    """Top 15 por taxa de óbitos / 10 mil hab. / ano."""
    taxas = serie_taxa(ano_min, ano_max)
    top = taxas.head(15)
    if top.empty:
        return None, "Sem população de referência para calcular a taxa."
    nome = nome_ararangua()
    cores = [TERTIARY if m == nome else PRIMARY for m in top.index]
    fig = bar_horizontal(
        top.round(1),
        f"Top 15 SC — óbitos/10 mil hab./ano — {periodo}",
        False,
        cores,
    )
    return fig, _insight_top_n(
        taxas, top, nome, "óbitos/10 mil hab./ano", normalizado=True
    )


def ocorrencia_por_municipio(df: pd.DataFrame, periodo: str):
    """Onde morreram os residentes de Araranguá."""
    from charts.texto import historia_volume, n_br, pct_br

    serie = df["CODMUNOCOR_NOME"].value_counts().head(10)
    fig = bar_horizontal(
        serie, f"Óbitos de residentes de Araranguá por município de ocorrência — {periodo}"
    )
    n_fora = int(df["OCORREU_FORA_RESIDENCIA"].sum())
    pct = 100 * n_fora / len(df) if len(df) else 0
    return fig, (
        historia_volume(len(df), periodo, serie, "óbitos de residentes")
        + f" Fora do município: {n_br(n_fora)} ({pct_br(pct)}%)."
    )


def _insight_top_n(
    ranking_completo,
    top,
    nome: str,
    unidade: str,
    normalizado: bool = False,
) -> str:
    """Texto alinhado ao top N do gráfico + posição completa de Araranguá."""
    from charts.texto import _num, n_br

    if top.empty:
        return "Sem dados para o ranking estadual."
    lider = top.index[0]
    topo = float(top.iloc[0])
    pref = "Normalizado pela população, o " if normalizado else "O "
    texto = (
        f"{pref}gráfico mostra o top {len(top)}. "
        f'Neste recorte, "{lider}" lidera ({_num(topo)} {unidade}).'
    )
    lugar = posicao(ranking_completo, nome)
    if lugar is None:
        return texto + f" {nome} não foi localizada no ranking completo."
    valor = float(ranking_completo.loc[nome]) if nome in ranking_completo.index else 0.0
    texto += (
        f" No ranking completo ({n_br(len(ranking_completo))} municípios), "
        f"{nome} está na {lugar}ª posição ({_num(valor)} {unidade})."
    )
    if nome not in top.index:
        texto += f" Por isso {nome} não aparece neste top {len(top)}."
    return texto
