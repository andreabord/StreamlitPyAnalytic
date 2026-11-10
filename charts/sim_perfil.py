"""Gráficos de perfil (ano, mês, idade, sexo, raça, escolaridade, local, causas)."""

from __future__ import annotations

import pandas as pd

from charts.theme import TERTIARY, bar_horizontal, bar_vertical
from data.constants import MAPA_ESC_CURTO, MAPA_LOCAL_CURTO, NOMES_MESES, ROTULOS_FAIXAS


def obitos_por_ano(df: pd.DataFrame, periodo: str):
    """A1: Série histórica anual com linha de média."""
    serie = df["ANO_OBITO"].value_counts().sort_index()
    fig = bar_vertical(serie, f"Óbitos por ano — Araranguá, {periodo}", False)
    media = float(serie.mean()) if len(serie) else 0
    fig.add_hline(
        y=media,
        line_dash="dash",
        line_color=TERTIARY,
        annotation_text=f"Média ({media:.0f})",
    )
    if serie.empty:
        return fig, "Sem dados anuais de óbitos."
    ano_min, ano_max = int(serie.index.min()), int(serie.index.max())
    pico, n = serie.idxmax(), int(serie.max())
    insight = (
        f"Entre {ano_min} e {ano_max}, Araranguá registrou de {int(serie.min())} a {n} "
        f"mortes de moradores por ano. O pico foi em {int(pico)} ({n} óbitos); "
        f"a média do período é {media:.0f} por ano."
    )
    return fig, insight


def media_por_mes(df: pd.DataFrame, periodo: str):
    """A2: Média de óbitos em cada mês do calendário."""
    validos = df.dropna(subset=["ANO_OBITO", "MES_OBITO"])
    tabela = validos.groupby(["ANO_OBITO", "MES_OBITO"]).size().unstack("MES_OBITO")
    media = tabela.mean(axis=0, skipna=True).reindex(range(1, 13))
    media.index = list(NOMES_MESES)
    fig = bar_vertical(
        media.fillna(0),
        f"Em média, quantas pessoas morrem em cada mês — Araranguá, {periodo}",
        False,
    )
    if media.dropna().empty:
        return fig, "Sem média mensal calculável."
    maior, menor = media.idxmax(), media.idxmin()
    insight = (
        f"Morrem mais pessoas em {maior.lower()} (média {media.max():.1f}). "
        f"O menor valor é {menor.lower()} ({media.min():.1f})."
    )
    return fig, insight


def obitos_por_faixa(df: pd.DataFrame, periodo: str):
    """A3: Distribuição por faixa etária."""
    serie = df["FAIXA_ETARIA"].value_counts().reindex(ROTULOS_FAIXAS).fillna(0)
    fig = bar_vertical(serie, f"Óbitos por faixa etária — Araranguá, {periodo}")
    total = float(serie.sum()) or 1
    idoso = serie[[f for f in serie.index if str(f).startswith(("60", "70", "80", "90"))]].sum()
    lider = serie.idxmax()
    bebes = float(serie.get("<1", 0))
    insight = (
        f"{100 * idoso / total:.1f}% das mortes ocorreram a partir dos 60 anos; "
        f"a faixa “{lider}” concentra {100 * serie.max() / total:.1f}% ({int(serie.max()):,}). "
        f"Menores de 1 ano somam {int(bebes):,} ({100 * bebes / total:.1f}%)."
    ).replace(",", ".")
    return fig, insight


def obitos_por_sexo(df: pd.DataFrame, periodo: str):
    """A4: Óbitos por sexo."""
    serie = _sem_ignorado(df, "SEXO").value_counts()
    fig = bar_vertical(serie, f"Óbitos por sexo — Araranguá, {periodo}")
    total = float(serie.sum()) or 1
    homens = int(serie.get("Masculino", 0))
    mulheres = int(serie.get("Feminino", 0))
    razao = (10 * homens / mulheres) if mulheres else 0
    insight = (
        f"{100 * homens / total:.1f}% das mortes foram de homens ({homens:,}) e "
        f"{100 * mulheres / total:.1f}% de mulheres ({mulheres:,})"
        + (f": cerca de {razao:.0f} homens para cada 10 mulheres." if mulheres else ".")
    ).replace(",", ".")
    return fig, insight


def obitos_por_raca(df: pd.DataFrame, periodo: str):
    """A5: Óbitos por raça/cor."""
    n_total = len(df)
    n_ign = int(df["RACACOR"].isin({"Ignorado"}).sum()) if n_total else 0
    serie = _sem_ignorado(df, "RACACOR").value_counts()
    fig = bar_vertical(serie, f"Óbitos por raça/cor — Araranguá, {periodo}")
    pct_ign = 100 * n_ign / n_total if n_total else 0
    lider = serie.index[0] if len(serie) else "—"
    insight = (
        f"Em {pct_ign:.1f}% das mortes a raça/cor não foi informada. "
        f"Entre as com informação, “{lider}” lidera. "
        "Essa distribuição reflete os registros, não a composição da população."
    )
    return fig, insight


def obitos_por_escolaridade(df: pd.DataFrame, periodo: str):
    """A6: Óbitos por escolaridade."""
    n_total = len(df)
    n_info = int((~df["ESC2010"].isin({"Ignorado"})).sum()) if n_total else 0
    serie = _sem_ignorado(df, "ESC2010").value_counts()
    curtos = serie.rename(index=lambda c: MAPA_ESC_CURTO.get(c, c))
    ordem = [
        "Sem escolaridade",
        "Fundamental I (1ª a 4ª)",
        "Fundamental II (5ª a 8ª)",
        "Médio",
        "Superior",
    ]
    curtos = curtos.reindex([k for k in ordem if k in curtos.index]).fillna(0)
    fig = bar_vertical(curtos, f"Óbitos por escolaridade — Araranguá, {periodo}")
    pct_info = 100 * n_info / n_total if n_total else 0
    lider = curtos.idxmax() if len(curtos) else "—"
    insight = (
        f"A escolaridade foi informada em {pct_info:.1f}% das mortes. "
        f"Entre elas, “{lider}” concentra a maior parte."
    )
    return fig, insight


def obitos_por_local(df: pd.DataFrame, periodo: str):
    """A7: Local de ocorrência."""
    serie = _sem_ignorado(df, "LOCOCOR").value_counts()
    curtos = serie.rename(index=lambda c: MAPA_LOCAL_CURTO.get(c, c))
    fig = bar_horizontal(curtos, f"Local de ocorrência dos óbitos — Araranguá, {periodo}")
    total = float(curtos.sum()) or 1

    def _pct(nome: str) -> float:
        return 100 * float(curtos.get(nome, 0)) / total

    insight = (
        f"{_pct('Hospital'):.1f}% ocorreram em hospital, {_pct('Domicílio'):.1f}% em casa "
        f"e {_pct('Via pública'):.1f}% na via pública."
    )
    return fig, insight


def top_causas(df: pd.DataFrame, periodo: str):
    """A8: Principais causas de óbito."""
    from charts.texto import historia_volume

    bruto = df["CAUSABAS_DESC"].value_counts()
    serie = bruto.head(10)
    fig = bar_horizontal(serie, f"Principais causas de óbito (top 10) — Araranguá, {periodo}")
    if serie.empty:
        return fig, "Sem causas básicas preenchidas."
    return fig, historia_volume(int(bruto.sum()), periodo, serie, "óbitos com causa básica")


def _sem_ignorado(df: pd.DataFrame, col: str) -> pd.Series:
    """Série sem Ignorado, como no notebook."""
    return df.loc[~df[col].isin({"Ignorado"}), col]
