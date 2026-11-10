"""Resumo editorial para a abertura dos hubs de dados."""

from html import escape

import streamlit as st


def render_highlights(
    pergunta: str,
    contexto: str,
    itens: list[tuple[str, str, str]],
) -> None:
    """Apresenta a pergunta da base e seus principais achados."""
    st.markdown(
        '<section class="hub-hero">'
        '<p class="hub-eyebrow">VISÃO RÁPIDA DA BASE</p>'
        f'<h1>{escape(pergunta)}</h1>'
        f'<p>{escape(contexto)}</p>'
        '</section>',
        unsafe_allow_html=True,
    )
    cards = "".join(_card(*item) for item in itens)
    st.markdown(
        f'<div class="hub-highlights">{cards}</div>',
        unsafe_allow_html=True,
    )


def render_topics(titulo: str = "O que você quer descobrir?") -> None:
    """Introduz a grade de histórias disponíveis."""
    st.markdown(
        '<div class="hub-topics-heading">'
        '<p class="hub-eyebrow">CONTINUE EXPLORANDO</p>'
        f'<h2>{escape(titulo)}</h2>'
        '</div>',
        unsafe_allow_html=True,
    )


def numero(valor: int | float) -> str:
    """Número no padrão brasileiro."""
    return f"{valor:,.0f}".replace(",", ".")


def reais(valor: float) -> str:
    """Valor monetário compacto no padrão brasileiro."""
    if abs(valor) >= 1_000_000:
        return f"R$ {valor / 1_000_000:.1f} mi".replace(".", ",")
    if abs(valor) >= 1_000:
        return f"R$ {valor / 1_000:.1f} mil".replace(".", ",")
    return f"R$ {valor:,.0f}".replace(",", ".")


def _card(rotulo: str, valor: str, detalhe: str) -> str:
    """Um highlight, com valor textual ou numérico."""
    classe = " is-text" if len(str(valor)) > 16 else ""
    return (
        '<article class="hub-highlight-card">'
        f'<p class="hub-highlight-label">{escape(str(rotulo))}</p>'
        f'<p class="hub-highlight-value{classe}">{escape(str(valor))}</p>'
        f'<p class="hub-highlight-detail">{escape(str(detalhe))}</p>'
        '</article>'
    )
