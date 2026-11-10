"""Gráficos: distribuição por bairro da pessoa vacinada."""

from __future__ import annotations

import pandas as pd

from charts.theme import bar_horizontal
from charts.texto import historia_volume, vazio
from charts.vac_common import com_data, ranking_barras
from charts.vac_tempo import bairros_no_tempo


def ranking_bairros(df: pd.DataFrame, periodo: str):
    """Bairros com mais pessoas vacinadas registradas."""
    return ranking_barras(df, "bairro", f"Aplicações por bairro — {periodo}", n=15)


def evolucao_top_bairros(df: pd.DataFrame, periodo: str):
    """Tendência mensal dos bairros líderes."""
    return bairros_no_tempo(df, periodo, n=5)


def vacina_lider_por_bairro(df: pd.DataFrame, periodo: str, n_bairros: int = 8):
    """Volume da vacina mais aplicada em cada bairro (top bairros)."""
    base = com_data(df)
    col_vac = "vacina_curta" if "vacina_curta" in base.columns else "nome_da_vacina"
    tops = base["bairro"].value_counts().head(n_bairros).index
    linhas = []
    for bairro in tops:
        parte = base.loc[base["bairro"] == bairro, col_vac].value_counts()
        if parte.empty:
            continue
        linhas.append(
            {
                "Bairro": bairro,
                "Vacina líder": parte.index[0],
                "Aplicações": int(parte.iloc[0]),
            }
        )
    tab = pd.DataFrame(linhas)
    if tab.empty:
        return vazio()
    fig = bar_horizontal(
        tab.set_index("Bairro")["Aplicações"],
        f"Volume da vacina líder em cada bairro — {periodo}",
    )
    lider = tab.loc[tab["Aplicações"].idxmax()]
    insight = (
        f"No período {periodo}, cada barra é a vacina líder do bairro "
        f"(top {len(tab)} bairros). "
        f'O maior volume é em "{lider["Bairro"]}" com '
        f'"{lider["Vacina líder"]}" ({lider["Aplicações"]} aplicações).'
    )
    return fig, insight


def perfil_influenza_por_bairro(df: pd.DataFrame, periodo: str, n: int = 10):
    """Participação da influenza no total de cada bairro."""
    from charts.texto import _num

    base = com_data(df)
    tops = base["bairro"].value_counts().head(n).index
    base = base.loc[base["bairro"].isin(tops)]
    tot = base.groupby("bairro").size()
    infl = base.loc[base["eh_influenza"]].groupby("bairro").size()
    pct = ((infl / tot) * 100).reindex(tot.index).fillna(0).sort_values(ascending=True)
    if pct.empty:
        return vazio()
    fig = bar_horizontal(pct, f"% de influenza no total do bairro — {periodo}", mostrar_pct=False)
    fig.update_xaxes(title="% das aplicações do bairro")
    maior = pct.index[-1]
    menor = pct.index[0]
    return fig, (
        f"Entre os {len(pct)} bairros com mais aplicações ({periodo}), "
        f'a maior participação de influenza é em "{maior}" ({_num(float(pct.iloc[-1]))}%) '
        f'e a menor em "{menor}" ({_num(float(pct.iloc[0]))}%). '
        f"Média neste recorte: {_num(float(pct.mean()))}%."
    )
