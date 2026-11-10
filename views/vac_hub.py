"""Hub da base Vacinações: análises, problema, fonte e links."""

import streamlit as st

from catalog import TOPICS_VAC
from components.carousel import html_analises
from components.highlights import numero, render_highlights, render_topics
from components.voltar import faixa_titulo
from data.kpis_vac import resumo_home_vac
from data.prepare_vac import load_vac
from views.vac_bairros import render as render_bairros
from views.vac_destaques import render as render_destaques
from views.vac_doses import render as render_doses
from views.vac_estrategias import render as render_estrategias
from views.vac_lotes import render as render_lotes
from views.vac_origem import render as render_origem
from views.vac_tempo import render as render_tempo

_TEMAS = {
    "tempo": render_tempo,
    "destaques": render_destaques,
    "bairros": render_bairros,
    "salas-bairros": render_bairros,  # URL antiga
    "estrategias": render_estrategias,
    "doses": render_doses,
    "origem": render_origem,
    "lotes": render_lotes,
}


def render() -> None:
    """Visão geral (/vacinas) ou um tema (/vacinas?tema=tempo)."""
    tema = st.query_params.get("tema", "")
    destino = _TEMAS.get(tema)
    if callable(destino):
        destino()
        return
    _visao_geral()


def _visao_geral() -> None:
    """Página central da base de vacinações."""
    with st.container(key="hub_base"):
        faixa_titulo("Vacinações — Araranguá", "home")
        _destaques()
        render_topics()
        st.html(html_analises(TOPICS_VAC))
        st.markdown("## Sobre a base")
        st.markdown(
            "### O problema\n"
            "Ver **quando, onde (bairro da pessoa) e como** as vacinas foram aplicadas "
            "ajuda a cidade a acompanhar o serviço sem confundir aplicação com cobertura "
            "da população."
        )
        st.markdown(
            "### A base\n"
            "Aplicações de vacinas em **Araranguá (fev–jun/2026)**: cerca de "
            "**31 mil** registros em **15 bairros**, com vacina, dose, estratégia, "
            "origem do registro, lote e validade. O bairro é o da pessoa vacinada — "
            "não a unidade de aplicação. Pacientes estão anonimizados."
        )


def _destaques() -> None:
    """Quatro leituras rápidas das aplicações registradas."""
    df = load_vac()
    kpis = resumo_home_vac(df)
    com_data = df.dropna(subset=["data_aplicacao"])
    meses = com_data["data_aplicacao"].dt.strftime("%m/%Y").value_counts()
    bairros = df["bairro"].dropna().astype(str).value_counts()
    pico = str(meses.index[0]) if not meses.empty else "Sem dados"
    bairro = str(bairros.index[0]) if not bairros.empty else "Sem dados"
    render_highlights(
        "Como está a vacinação registrada em Araranguá?",
        f"Aplicações em Araranguá · {kpis['periodo']} · dados anonimizados",
        [
            ("Aplicações", numero(kpis["total"]), f"{numero(kpis['vacinas'])} vacinas diferentes"),
            ("Vacina mais aplicada", kpis["top_vacina"], f"{kpis['top_pct']:.1f}% das aplicações com data"),
            ("Mês com mais registros", pico, "maior volume de aplicações"),
            ("Bairro com mais registros", bairro, "bairro da pessoa vacinada"),
        ],
    )
