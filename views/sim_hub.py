"""Hub da base SIM: análises, problema, fonte e links."""

import streamlit as st

from catalog import TOPICS_SIM
from components.carousel import html_analises
from components.highlights import numero, render_highlights, render_topics
from components.voltar import faixa_titulo
from data.kpis import resumo_home
from data.prepare_sim_retrato import load_retrato
from views.sim_evitavel import render as render_evitavel
from views.sim_local import render as render_local
from views.sim_materna import render as render_materna
from views.sim_retrato import render as render_retrato
from views.sim_violentas import render as render_violentas

API_SIM = (
    "https://apidadosabertos.saude.gov.br/vigilancia-e-meio-ambiente/"
    "sistema-de-informacao-sobre-mortalidade"
)
DOC_SIM = "https://datasus.saude.gov.br/mortalidade-desde-1996-pela-cid-10"


# Temas da SIM: /sim?tema=<slug> (Streamlit não aceita /sim/retrato).
_TEMAS = {
    "retrato": render_retrato,
    "evitavel": render_evitavel,
    "onde-morrem": render_local,
    "violentas": render_violentas,
    "materna": render_materna,
}


def render() -> None:
    """Visão geral (/sim) ou um tema (/sim?tema=retrato)."""
    visao = _TEMAS.get(st.query_params.get("tema", ""))
    if visao:
        visao()
        return
    _visao_geral()


def _visao_geral() -> None:
    """Página central da SIM, de onde saem os temas."""
    with st.container(key="hub_base"):
        faixa_titulo("SIM — Sistema de Informações sobre Mortalidade", "home")
        _destaques()
        render_topics()
        _grade()
        _sobre_a_base()


def _destaques() -> None:
    """Quatro leituras rápidas da mortalidade registrada."""
    df = load_retrato()
    kpis = resumo_home(df)
    faixa = _mais_frequente(df, "FAIXA_ETARIA")
    render_highlights(
        "O que os registros de mortalidade revelam sobre Araranguá?",
        f"Residentes de Araranguá · {kpis['periodo']} · Sistema de Informações sobre Mortalidade",
        [
            ("Óbitos registrados", numero(kpis["total"]), "no período analisado"),
            ("Causa mais frequente", kpis["causa"], f"{kpis['pct_causa']:.1f}% dos registros"),
            ("Faixa etária predominante", faixa, "maior frequência na base"),
            ("Ocorridos em hospital", f"{kpis['pct_hospital']:.0f}%", "local de ocorrência informado"),
        ],
    )


def _mais_frequente(df, coluna: str) -> str:
    """Moda textual segura para um destaque."""
    serie = df[coluna].dropna().astype(str)
    serie = serie[~serie.str.lower().isin({"ignorado", "não informado"})]
    return str(serie.value_counts().index[0]) if not serie.empty else "Sem informação"


def _grade() -> None:
    """Cards iguais: 3 na primeira linha, 2 na segunda."""
    st.html(html_analises(TOPICS_SIM))


def _sobre_a_base() -> None:
    """Contexto da SIM: problema, recorte e fontes."""
    st.markdown("## Sobre a base")
    _problema()
    _base()
    _links()


def _problema() -> None:
    """Por que olhar mortalidade em Araranguá."""
    st.markdown("### O problema")
    st.markdown(
        "Saber **quem morre, de quê, onde e com qual perfil** ajuda a cidade a "
        "enxergar desigualdades, causas evitáveis e a rede de cuidado. Sem um "
        "painel público, esses números ficam presos em planilhas do DATASUS."
    )


def _base() -> None:
    """O que é a SIM e o recorte usado."""
    st.markdown("### A base")
    st.markdown(
        "A **SIM** registra as Declarações de Óbito no Brasil. Neste portal "
        "usamos o recorte de **residentes de Araranguá (SC)**, com colunas já "
        "tratadas pelo pipeline do PyAnalytics (sexo, raça/cor, local, idade, causa)."
    )


def _links() -> None:
    """Fontes oficiais para quem quiser ir além do painel."""
    st.markdown("### Links")
    st.markdown(f"- [API de Dados Abertos — SIM]({API_SIM})")
    st.markdown(f"- [Documentação DATASUS (CID-10)]({DOC_SIM})")
