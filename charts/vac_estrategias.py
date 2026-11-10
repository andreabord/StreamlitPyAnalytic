"""Gráficos: estratégias de vacinação."""

from __future__ import annotations

import re

import pandas as pd

from charts.theme import heatmap
from charts.texto import vazio
from charts.vac_common import com_data, ranking_barras, serie_mensal_grupo, linhas_por_grupo

_MESES = {
    "01": "janeiro", "02": "fevereiro", "03": "março", "04": "abril",
    "05": "maio", "06": "junho", "07": "julho", "08": "agosto",
    "09": "setembro", "10": "outubro", "11": "novembro", "12": "dezembro",
}
_EXTENSO = {1: "uma", 2: "duas", 3: "três", 4: "quatro", 5: "cinco", 6: "seis",
            7: "sete", 8: "oito", 9: "nove", 10: "dez"}


# ---------- auxiliares de texto ----------

def _n(valor) -> str:
    """Número com ponto de milhar (pt-BR)."""
    return f"{int(valor):,}".replace(",", ".")


def _pct(valor: float) -> str:
    """Percentual com uma casa e vírgula."""
    return f"{valor:.1f}".replace(".", ",")


def _rotulo(nome) -> str:
    """O código "19" da estratégia corresponde à vacina Covid-19."""
    return "Covid-19" if str(nome) == "19" else str(nome)


def _lista(itens: list[str]) -> str:
    """Junta itens como 'a, b e c'."""
    if len(itens) <= 1:
        return "".join(itens)
    return ", ".join(itens[:-1]) + " e " + itens[-1]


def _vacina_curta(nome) -> str:
    """'Vacina dengue (atenuada)' -> 'dengue'."""
    texto = re.sub(r"^Vacina\s+", "", str(nome))
    return re.sub(r"\s*\(.*\)\s*$", "", texto).strip()


def _com_texto(resultado, texto: str | None):
    """Troca o texto de um (figura, texto); mantém o resultado se for vazio."""
    if texto and isinstance(resultado, tuple) and len(resultado) == 2 and resultado[0] is not None:
        return resultado[0], texto
    return resultado


# ---------- histórias ----------

def _historia_frequencia(df: pd.DataFrame, periodo: str) -> str | None:
    base = com_data(df)
    contagem = base["estrategia"].value_counts()
    total = int(contagem.sum())
    if total == 0 or len(contagem) < 2:
        return None
    (a, na), (b, nb) = list(contagem.items())[:2]
    texto = (
        f"Entre {periodo.replace(' a ', ' e ')}, Araranguá registrou {_n(total)} aplicações de vacina. "
        f"A estratégia {_rotulo(a)} concentra {_pct(na / total * 100)}% ({_n(na)}) "
        f"e a {_rotulo(b)} {_pct(nb / total * 100)}% ({_n(nb)})."
    )
    outras = contagem.iloc[2:]
    if not outras.empty:
        soma = int(outras.sum())
        partes = list(outras.head(2).items())
        covid = next((k for k in outras.index if str(k) in ("19", "Covid-19")), None)
        if covid is not None and covid not in [k for k, _ in partes]:
            partes.append((covid, outras[covid]))
        exemplos = _lista([f"{_rotulo(k)} ({_n(v)})" for k, v in partes])
        qtd = _EXTENSO.get(len(outras), str(len(outras)))
        texto += (
            f" As outras {qtd} somam {_n(soma)} aplicações ({_pct(soma / total * 100)}%), "
            f"como {exemplos}; percentuais abaixo de 0,05% aparecem como 0,0%."
        )
    return texto


def _mes(chave: str) -> str:
    return _MESES.get(chave[5:], chave[5:])


def _trecho_serie(nome: str, serie: pd.Series, primeiro: bool) -> str:
    inicio, fim = serie.index[0], serie.index[-1]
    pico = serie.idxmax()
    v0, vp, vf = int(serie.iloc[0]), int(serie.max()), int(serie.iloc[-1])
    if primeiro and v0 < vp and vf < vp:
        return (f"A {nome} subiu de {_n(v0)} aplicações em {_mes(inicio)} para o pico de "
                f"{_n(vp)} em {_mes(pico)}, e caiu para {_n(vf)} em {_mes(fim)}.")
    if not primeiro and v0 < vp:
        return (f"A {nome} começou com {_n(v0)} em {_mes(inicio)}, cresceu até o pico de "
                f"{_n(vp)} em {_mes(pico)} e ficou em {_n(vf)} em {_mes(fim)}.")
    return (f"A {nome} teve {_n(v0)} aplicações em {_mes(inicio)}, pico de {_n(vp)} "
            f"em {_mes(pico)} e {_n(vf)} em {_mes(fim)}.")


def _historia_tempo(df: pd.DataFrame) -> str | None:
    base = com_data(df)
    if base.empty or "ano_mes" not in base.columns:
        return None
    tab = base.groupby(["ano_mes", "estrategia"]).size().unstack(fill_value=0).sort_index()
    principais = [e for e in base["estrategia"].value_counts().index[:2] if e in tab.columns]
    if len(principais) < 2 or len(tab) < 2:
        return None
    partes = [
        _trecho_serie(_rotulo(principais[0]), tab[principais[0]], primeiro=True),
        _trecho_serie(_rotulo(principais[1]), tab[principais[1]], primeiro=False),
    ]
    raras = [c for c in ("Pós-exposição", "Intensificação") if c in tab.columns]
    if raras:
        teto = int(tab[raras].max().max())
        partes.append(f"{' e '.join(raras)} não passam de {_n(teto)} aplicações por mês.")
    return " ".join(partes)


def _historia_cruzamento(tab: pd.DataFrame) -> str | None:
    if tab.shape[0] < 2 or tab.shape[1] < 2:
        return None
    e1, e2 = list(tab.sum(axis=0).sort_values(ascending=False).index[:2])
    topo = tab.index[0]  # a tabela já vem ordenada por volume
    texto = (
        f"A vacina de {_vacina_curta(topo)} domina as duas maiores estratégias: "
        f"{_n(tab.loc[topo, e1])} aplicações na {_rotulo(e1)} e {_n(tab.loc[topo, e2])} na {_rotulo(e2)}."
    )
    demais = tab.drop(index=topo).sort_values(e1, ascending=False).head(3)
    exemplos = _lista([f"{_vacina_curta(v)} ({_n(demais.loc[v, e1])})" for v in demais.index])
    texto += (
        f" Nas demais vacinas, quase tudo é {_rotulo(e1)}: {exemplos}. "
        "Cada célula mostra quantas aplicações daquela vacina ocorreram naquela estratégia."
    )
    return texto


# ---------- gráficos ----------

def ranking_estrategias(df: pd.DataFrame, periodo: str):
    """Frequência das estratégias na base."""
    resultado = ranking_barras(df, "estrategia", f"Estratégias de vacinação — {periodo}", n=12)
    return _com_texto(resultado, _historia_frequencia(df, periodo))


def evolucao_estrategias(df: pd.DataFrame, periodo: str, n: int = 4):
    """Estratégias principais no tempo."""
    tab = serie_mensal_grupo(df, "estrategia", top=n)
    resultado = linhas_por_grupo(
        tab,
        "estrategia",
        f"Estratégias ao longo do tempo — {periodo}",
        "Estratégia",
    )
    return _com_texto(resultado, _historia_tempo(df))


def cruzamento_vacina_estrategia(df: pd.DataFrame, periodo: str, n_vac: int = 8):
    """Heatmap vacina × estratégia (top vacinas)."""
    base = com_data(df)
    tops = base["nome_da_vacina"].value_counts().head(n_vac).index
    tab = (
        base.loc[base["nome_da_vacina"].isin(tops)]
        .pivot_table(
            index="nome_da_vacina",
            columns="estrategia",
            values="data_aplicacao",
            aggfunc="count",
            fill_value=0,
        )
    )
    if tab.empty:
        return vazio()
    tab.index.name = "Vacina"
    tab.columns.name = "Estratégia"
    # ordena por volume
    tab = tab.loc[tab.sum(axis=1).sort_values(ascending=False).index]
    fig = heatmap(tab, f"Vacina × estratégia (top {n_vac}) — {periodo}", cor_legenda="Aplicações")
    return fig, _historia_cruzamento(tab) or ""


def estrategias_raras(df: pd.DataFrame, periodo: str, limiar: int = 50):
    """Estratégias com pouco volume (barras). Mantida por compatibilidade."""
    serie = com_data(df)["estrategia"].value_counts()
    rara = serie[serie < limiar].sort_values(ascending=True)
    if rara.empty:
        return vazio("Não há estratégias abaixo do limiar.")
    from charts.theme import bar_horizontal

    fig = bar_horizontal(rara, f"Estratégias menos frequentes (< {limiar}) — {periodo}")
    fig.update_xaxes(title="Número de aplicações")
    return fig, f"{len(rara)} estratégia(s) com menos de {limiar} aplicações."
