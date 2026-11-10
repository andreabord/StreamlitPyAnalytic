"""Gráficos: origem do registro da aplicação."""

from __future__ import annotations

import re

import pandas as pd
import plotly.express as px

from charts.texto import insight_top, vazio
from charts.vac_common import (
    com_data,
    linhas_por_grupo,
    ranking_barras,
    serie_mensal_grupo,
)

_CART, _PRONT, _TELA, _NI = "Carteirinha", "Prontuário", "Tela de Aplicação", "Não informado"

_MESES = {
    "01": "janeiro", "02": "fevereiro", "03": "março", "04": "abril",
    "05": "maio", "06": "junho", "07": "julho", "08": "agosto",
    "09": "setembro", "10": "outubro", "11": "novembro", "12": "dezembro",
}
_EXTENSO = {1: "um", 2: "dois", 3: "três", 4: "quatro", 5: "cinco",
            6: "seis", 7: "sete", 8: "oito", 9: "nove", 10: "dez"}


# ---------- auxiliares de texto ----------

def _n(valor) -> str:
    """Número com ponto de milhar (pt-BR)."""
    return f"{int(valor):,}".replace(",", ".")


def _pct(valor: float) -> str:
    """Percentual com uma casa e vírgula."""
    return f"{valor:.1f}".replace(".", ",")


def _inteiro(valor: float) -> str:
    return f"{round(valor)}"


def _mes(chave: str) -> str:
    """'2026-02' -> 'fevereiro'."""
    return _MESES.get(chave[5:], chave[5:])


def _periodo_texto(periodo: str) -> str:
    """'02/2026 a 06/2026' -> 'de fevereiro a junho de 2026'."""
    m = re.match(r"(\d{2})/(\d{4}) a (\d{2})/(\d{4})", periodo)
    if not m:
        return periodo
    m1, a1, m2, a2 = m.groups()
    if a1 == a2:
        return f"de {_MESES[m1]} a {_MESES[m2]} de {a1}"
    return f"de {_MESES[m1]} de {a1} a {_MESES[m2]} de {a2}"


def _com_texto(resultado, texto: str | None):
    """Troca o texto de um (figura, texto); mantém o resultado se for vazio."""
    if texto and isinstance(resultado, tuple) and len(resultado) == 2 and resultado[0] is not None:
        return resultado[0], texto
    return resultado


def _col(tab: pd.DataFrame, nome: str) -> pd.Series:
    """Coluna da tabela ou zeros, se a origem não existir."""
    if nome in tab.columns:
        return tab[nome]
    return pd.Series(0, index=tab.index)


# ---------- histórias ----------

def _historia_volume(df: pd.DataFrame, periodo: str) -> str | None:
    total = len(df)
    contagem = df["origem"].value_counts()
    informados = int(total - contagem.get(_NI, 0))
    if total == 0 or informados == 0:
        return None
    cart, pront, tela = (int(contagem.get(o, 0)) for o in (_CART, _PRONT, _TELA))
    p_cart = cart / informados * 100
    texto = (
        f"A base tem {_n(total)} registros de aplicação, {_periodo_texto(periodo)}. "
        f"Em {_n(informados)} deles a origem do registro está informada: "
        f"{round(p_cart / 10)} em cada 10 ({_pct(p_cart)}%; {_n(cart)}) vieram da carteirinha, "
        f"{_pct(pront / informados * 100)}% ({_n(pront)}) do prontuário e "
        f"{_pct(tela / informados * 100)}% ({_n(tela)}) da tela de aplicação."
    )
    sem = total - informados
    if sem:
        texto += (
            f" Outros {_n(sem)} registros ({_pct(sem / total * 100)}%) não têm origem informada "
            "e aparecem como \"Não informado\"."
        )
    return texto


def _historia_tempo(df: pd.DataFrame) -> str | None:
    base = com_data(df)
    base = base[base["origem"] != _NI]
    if base.empty or "ano_mes" not in base.columns:
        return None
    tab = base.groupby(["ano_mes", "origem"]).size().unstack(fill_value=0).sort_index()
    if len(tab) < 2:
        return None
    pcts = tab.div(tab.sum(axis=1), axis=0) * 100
    cart, pront, tela = (_col(pcts, o) for o in (_CART, _PRONT, _TELA))
    ini, fim, pico = cart.index[0], cart.index[-1], cart.idxmax()

    abertura = "Em todos os meses, a maior parte dos registros vem da carteirinha" if (cart > 50).all() \
        else "A carteirinha responde por parte dos registros de cada mês"
    if cart.iloc[0] < cart.max() and cart.iloc[-1] < cart.max():
        frase_cart = (f"{abertura}: de {_pct(cart.iloc[0])}% em {_mes(ini)} a {_pct(cart.max())}% "
                      f"em {_mes(pico)}, com queda para {_pct(cart.iloc[-1])}% em {_mes(fim)}.")
    else:
        frase_cart = (f"{abertura}: {_pct(cart.iloc[0])}% em {_mes(ini)} e "
                      f"{_pct(cart.iloc[-1])}% em {_mes(fim)}.")
    frase_pront = (
        f"O prontuário ocupa entre {_pct(pront.min())}% ({_mes(pront.idxmin())}) e "
        f"{_pct(pront.max())}% ({_mes(pront.idxmax())}) dos registros do mês, "
    )
    verbo = "cai" if tela.iloc[-1] < tela.iloc[0] else "vai"
    frase_tela = (f"e a tela de aplicação {verbo} de {_pct(tela.iloc[0])}% em {_mes(ini)} "
                  f"para {_pct(tela.iloc[-1])}% em {_mes(fim)}.")
    return f"{frase_cart} {frase_pront}{frase_tela}"


def _historia_bairros(tab: pd.DataFrame) -> str | None:
    if tab.empty:
        return None
    totais = tab.sum(axis=1)
    pcts = tab.div(totais, axis=0) * 100
    cart, pront, tela = _col(pcts, _CART), _col(pcts, _PRONT), _col(tab, _TELA)
    n_bairros = len(tab)
    n_cart = int((cart > 98).sum())
    texto = (
        "Cada barra mostra de onde vêm os registros de aplicação em um bairro; "
        "os percentuais abaixo são calculados sobre o total de cada bairro. "
        f"Em {_EXTENSO.get(n_cart, n_cart)} dos {_EXTENSO.get(n_bairros, n_bairros)} bairros mostrados, "
        "mais de 98% vêm da carteirinha."
    )
    altos = pront[pront >= 50].sort_values(ascending=False)
    if not altos.empty:
        nomes = list(altos.items())
        texto += f" Em {nomes[0][0]}, {_inteiro(nomes[0][1])}% vêm do prontuário"
        if len(nomes) > 1:
            texto += ", e " + ", ".join(f"em {b}, {_inteiro(p)}%" for b, p in nomes[1:])
        texto += "."
    total_tela = int(tela.sum())
    if total_tela == 0:
        texto += " A tela de aplicação não aparece nesses bairros."
    else:
        com_tela = tela[tela > 0]
        onde = f", em {com_tela.index[0]}" if len(com_tela) == 1 else ""
        texto += f" A tela de aplicação quase não aparece nesses bairros ({_n(total_tela)} registros{onde})."
    return texto


# ---------- gráficos ----------

def ranking_origem(df: pd.DataFrame, periodo: str):
    """Volume por origem do registro."""
    resultado = ranking_barras(df, "origem", f"Origem do registro — {periodo}", n=8)
    return _com_texto(resultado, _historia_volume(df, periodo))


def evolucao_origem(df: pd.DataFrame, periodo: str):
    """Origens ao longo do tempo."""
    tab = serie_mensal_grupo(df, "origem", top=5)
    resultado = linhas_por_grupo(
        tab, "origem", f"Origem do registro no tempo — {periodo}", "Origem"
    )
    return _com_texto(resultado, _historia_tempo(df))


def origem_por_bairro(df: pd.DataFrame, periodo: str, n_bairros: int = 8):
    """Gráfico de barras horizontais 100% empilhadas: Bairro × origem."""
    base = com_data(df)
    tops = base["bairro"].value_counts().head(n_bairros).index
    tab = (
        base.loc[base["bairro"].isin(tops)]
        .pivot_table(
            index="bairro",
            columns="origem",
            values="data_aplicacao",
            aggfunc="count",
            fill_value=0,
        )
    )
    if tab.empty:
        return vazio()
    
    tab = tab.loc[tab.sum(axis=1).sort_values(ascending=False).index]

    # Barras 100% empilhadas (auditoria) + texto dinâmico por bairro
    tab_perc = tab.div(tab.sum(axis=1), axis=0) * 100
    df_plot = tab_perc.reset_index().melt(
        id_vars="bairro", var_name="Origem", value_name="Percentual"
    )
    fig = px.bar(
        df_plot,
        x="Percentual",
        y="bairro",
        color="Origem",
        orientation="h",
        title=f"Bairro × origem do registro (100% empilhado) — {periodo}",
        labels={"Percentual": "Participação (%)", "bairro": "Bairro", "Origem": "Origem"},
    )
    fig.update_layout(
        barmode="stack",
        yaxis={"categoryorder": "total ascending"},
        xaxis_title="Participação (%)",
        yaxis_title="Bairro",
    )
    return fig, _historia_bairros(tab) or insight_top(base["origem"].value_counts())
