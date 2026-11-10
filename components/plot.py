"""Exibe gráfico Plotly + insight curto."""

import hashlib
from html import escape
import re

import streamlit as st

from charts.theme import adaptar_tema, tem_heatmap, tema_plotly


def plot(fig, insight: str | None = None) -> None:
    """Renderiza o gráfico em largura total, sem barra de ferramentas."""
    fig = adaptar_tema(fig)
    titulo = _extrair_titulo(fig)
    if insight:
        _insight(insight)
    st.markdown(
        '<p class="historia-evidencia">A evidência nos dados</p>',
        unsafe_allow_html=True,
    )
    if titulo:
        st.markdown(
            f'<p class="grafico-titulo">{escape(titulo)}</p>',
            unsafe_allow_html=True,
        )
    if tem_heatmap(fig):
        # O frontend do Streamlit mede primeiro a coluna estreita do celular.
        # Fixar também o canvas Plotly evita uma matriz pequena seguida de vazio.
        fig.update_layout(width=760, autosize=False)
        identidade = hashlib.sha1(titulo.encode("utf-8")).hexdigest()[:10]
        with st.container(key=f"heatmap_plot_{identidade}"):
            st.markdown(
                '<p class="heatmap-ajuda">Deslize para os lados e toque nas células '
                "para ver os valores.</p>",
                unsafe_allow_html=True,
            )
            _plotly(fig, width=760, responsive=False)
        return
    _plotly(fig)


def _extrair_titulo(fig) -> str:
    """Move o título para fora do canvas, onde ele quebra corretamente."""
    bruto = getattr(getattr(fig.layout, "title", None), "text", "") or ""
    texto = re.sub(r"<br\s*/?>", " ", str(bruto), flags=re.IGNORECASE)
    texto = " ".join(texto.split())
    if texto.lower() in {"undefined", "none", "null"}:
        texto = ""
    margem = fig.layout.margin.to_plotly_json() if fig.layout.margin else {}
    margem["t"] = 20
    # title=None vira "undefined" no Plotly.js — usar texto vazio
    fig.update_layout(title=dict(text=""), margin=margem)
    return texto


def _plotly(
    fig,
    width: str | int = "stretch",
    responsive: bool = True,
) -> None:
    """Renderiza a figura fixa: sem zoom, pan ou redimensionar ao clicar."""
    _travar_interacao(fig)
    st.plotly_chart(
        fig,
        width=width,
        theme=tema_plotly(fig),
        config={
            "displayModeBar": False,
            "responsive": responsive,
            "scrollZoom": False,
            "doubleClick": False,
            "showTips": False,
            "editable": False,
        },
    )


def _travar_interacao(fig) -> None:
    """Legenda continua ligando/desligando séries; escala e zoom ficam fixos."""
    fig.update_layout(
        dragmode=False,
        clickmode="event",
        legend=dict(itemclick="toggle", itemdoubleclick="toggleothers"),
    )
    _congelar_escalas(fig)
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)


def _congelar_escalas(fig) -> None:
    """Trava min/max para ocultar série na legenda não redimensionar o gráfico."""
    if tem_heatmap(fig):
        return
    ys = _valores_numericos(fig, "y")
    if ys:
        ymin, ymax = min(ys), max(ys)
        pad = (ymax - ymin) * 0.08 if ymax > ymin else abs(ymax or 1) * 0.08
        fig.update_yaxes(range=[ymin - pad, ymax + pad], autorange=False)
    xs = _valores_numericos(fig, "x")
    if xs:
        xmin, xmax = min(xs), max(xs)
        pad = (xmax - xmin) * 0.02 if xmax > xmin else 0.5
        fig.update_xaxes(range=[xmin - pad, xmax + pad], autorange=False)


def _valores_numericos(fig, eixo: str) -> list[float]:
    """Coleta valores numéricos de todos os traços (ignora categorias/texto)."""
    valores: list[float] = []
    for traco in fig.data:
        serie = getattr(traco, eixo, None)
        if serie is None:
            continue
        for item in serie:
            try:
                numero = float(item)
            except (TypeError, ValueError):
                continue
            if numero == numero:  # não NaN
                valores.append(numero)
    return valores


def plot_or_caption(fig, insight: str | None = None) -> None:
    """Mostra o gráfico ou só o recado, se não houver figura."""
    if fig is None:
        _insight(insight or "Sem dados para este gráfico.")
        return
    plot(fig, insight)


def _insight(texto: str) -> None:
    """Apresenta a conclusão antes da evidência visual."""
    seguro = escape(str(texto))
    st.markdown(
        '<div class="historia-significado"><strong>Descoberta em destaque</strong>'
        f"<p>{seguro}</p></div>",
        unsafe_allow_html=True,
    )
