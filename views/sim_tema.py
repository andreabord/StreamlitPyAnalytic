"""Cabeçalho e narrativa progressiva das páginas de análise."""

import hashlib
from html import escape
from urllib.parse import urlencode

import streamlit as st

from components.plot import plot_or_caption
from components.voltar import faixa_titulo
from navigation import href


def cabecalho(
    titulo: str,
    detalhe: str,
    voltar_id: str = "sim",
    total_descobertas: int | None = None,
) -> None:
    """Título da análise e, quando pedido, inicia a história paginada."""
    faixa_titulo(titulo, voltar_id)
    st.caption(detalhe)
    st.markdown('<span id="inicio-historia"></span>', unsafe_allow_html=True)
    if total_descobertas is None:
        st.session_state.pop("_historia_atual", None)
        return

    identidade = hashlib.sha1(titulo.encode("utf-8")).hexdigest()[:10]
    chave = f"historia_{identidade}"
    indice = _indice_url(total_descobertas)
    st.session_state[chave] = indice
    st.session_state["_historia_atual"] = {
        "chave": chave,
        "indice": indice,
        "total": total_descobertas,
        "contador": 0,
        "voltar_id": voltar_id,
    }
def secao(nome: str, *pares, extra=None) -> None:
    """Mostra um gráfico por descoberta; `extra` entra antes da navegação."""
    historia = st.session_state.get("_historia_atual")
    com_extra = extra is not None
    if historia is None:
        st.markdown(f"### {nome}")
        for par in pares:
            _mostra(par, texto_sem_figura=com_extra)
        if extra:
            extra()
        return

    # Sem figura e sem extra = não entra na história (evita "não há dados…")
    itens = _achatar(pares)
    if not com_extra:
        itens = [par for par in itens if not _sem_figura(par)]
    for numero, par in enumerate(itens, start=1):
        posicao = historia["contador"]
        historia["contador"] += 1
        if posicao != historia["indice"]:
            continue
        titulo = nome if len(itens) == 1 else f"{nome} · parte {numero} de {len(itens)}"
        _progresso(posicao, historia["total"])
        with st.container(key=f"descoberta_{historia['chave']}_{posicao}"):
            st.markdown('<p class="historia-kicker">DESTAQUE DA ANÁLISE</p>', unsafe_allow_html=True)
            st.markdown(f"## {titulo}")
            _mostra(par, texto_sem_figura=com_extra)
            if extra:
                extra()
        _navegacao(posicao, historia["total"], historia["voltar_id"])


def descoberta_ativa(posicao: int) -> bool:
    """True se a descoberta atual é a pedida (ou se não há modo história)."""
    historia = st.session_state.get("_historia_atual")
    return historia is None or historia["indice"] == posicao


def _progresso(indice: int, total: int) -> None:
    """Rótulo e trilha visual da posição atual."""
    preenchido = ((indice + 1) / total) * 100
    st.markdown(
        f'<div class="historia-progresso" aria-label="Descoberta {indice + 1} de {total}">'
        f'<span>{indice + 1} de {total} descobertas</span>'
        f'<div><i style="width:{preenchido:.2f}%"></i></div></div>',
        unsafe_allow_html=True,
    )


def _navegacao(indice: int, total: int, voltar_id: str) -> None:
    """Links reais: a âncora reposiciona o navegador sem depender do rerun."""
    if indice == 0:
        anterior = '<span class="historia-nav-link is-disabled">← Descoberta anterior</span>'
    else:
        anterior = _link_historia("← Descoberta anterior", indice - 1, "secondary")
    if indice < total - 1:
        proxima = _link_historia("Próxima descoberta →", indice + 1, "primary")
    else:
        destino = escape(href(voltar_id), quote=True)
        proxima = (
            f'<a class="historia-nav-link primary" href="{destino}" target="_self">'
            "Explorar outras histórias →</a>"
        )
    st.markdown(
        f'<nav class="historia-nav" aria-label="Navegação das descobertas">'
        f"{anterior}{proxima}</nav>",
        unsafe_allow_html=True,
    )


def _indice_url(total: int) -> int:
    """Lê ?descoberta= (1..N), usando a primeira quando inválido."""
    try:
        solicitado = int(st.query_params.get("descoberta", "1")) - 1
    except (TypeError, ValueError):
        solicitado = 0
    return max(0, min(solicitado, total - 1))


def _link_historia(rotulo: str, indice: int, classe: str) -> str:
    """Link relativo que preserva tema/recorte e aponta para o topo."""
    parametros = dict(st.query_params)
    parametros["descoberta"] = str(indice + 1)
    destino = "?" + urlencode(parametros, doseq=True) + "#inicio-historia"
    return (
        f'<a class="historia-nav-link {classe}" href="{escape(destino, quote=True)}" '
        f'target="_self">{rotulo}</a>'
    )


def _achatar(pares) -> list:
    """Transforma listas de figuras em capítulos individuais."""
    itens = []
    for par in pares:
        itens.extend(par if isinstance(par, list) else [par])
    return itens


def _sem_figura(par) -> bool:
    """True quando não há gráfico para mostrar."""
    if par is None:
        return True
    if isinstance(par, (tuple, list)) and len(par) >= 1:
        return par[0] is None
    return False


def _mostra(par, texto_sem_figura: bool = False) -> None:
    """Aceita (fig, insight) ou uma lista desses pares."""
    if par is None:
        return
    if isinstance(par, list):
        for item in par:
            _mostra(item, texto_sem_figura=texto_sem_figura)
        return
    if _sem_figura(par):
        # Só texto sem gráfico quando a seção tem `extra` (ex.: seletor)
        if texto_sem_figura and isinstance(par, tuple) and len(par) > 1 and par[1]:
            plot_or_caption(*par)
        return
    plot_or_caption(*par)
