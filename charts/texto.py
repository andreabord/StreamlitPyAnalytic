"""Histórias e textos dos gráficos (padrão narrativo, alinhado ao que o gráfico mostra)."""

from __future__ import annotations


def insight_top(serie, extra: str = "", universo: float | None = None) -> str:
    """História do ranking exibido; % sobre o universo (base) quando informado."""
    if serie is None or len(serie) == 0 or float(serie.sum()) == 0:
        return "Sem dados para este gráfico."
    ordenada = serie.sort_values(ascending=False)
    soma = float(ordenada.sum())
    denom = float(universo) if universo is not None and universo > 0 else soma
    lider = str(ordenada.index[0])
    n1 = int(ordenada.iloc[0])
    p1 = 100 * n1 / denom
    em10 = max(1, round(p1 / 10))
    ref = "da base" if universo is not None and abs(denom - soma) > 1e-6 else "do total"

    if em10 >= 5:
        texto = (
            f"{em10} em cada 10 ({pct_br(p1)}% {ref}; {n_br(n1)}) "
            f'correspondem a "{lider}"'
        )
    else:
        texto = (
            f'"{lider}" lidera com {n_br(n1)} ({pct_br(p1)}% {ref})'
        )

    if len(ordenada) >= 3:
        s2, s3 = str(ordenada.index[1]), str(ordenada.index[2])
        n2, n3 = int(ordenada.iloc[1]), int(ordenada.iloc[2])
        p2, p3 = 100 * n2 / denom, 100 * n3 / denom
        texto += (
            f', seguido de "{s2}" ({pct_br(p2)}%; {n_br(n2)}) '
            f'e "{s3}" ({pct_br(p3)}%; {n_br(n3)})'
        )
    elif len(ordenada) == 2:
        s2 = str(ordenada.index[1])
        n2 = int(ordenada.iloc[1])
        p2 = 100 * n2 / denom
        texto += f', seguido de "{s2}" ({pct_br(p2)}%; {n_br(n2)})'

    juntos = 100 * float(ordenada.head(min(3, len(ordenada))).sum()) / denom
    if len(ordenada) >= 2:
        texto += (
            f". Os {_extenso(min(3, len(ordenada)))} primeiros "
            f"somam {pct_br(juntos)}% {ref}"
        )
    texto += "."
    if extra:
        texto = f"{texto} {extra}".strip()
    return texto


def historia_volume(total: int, periodo: str, serie, sujeito: str) -> str:
    """Abertura com tamanho da base + ranking do que está no gráfico."""
    if total <= 0 or serie is None or len(serie) == 0:
        return "Sem dados para este gráfico."
    abertura = f"A base tem {n_br(total)} {sujeito}, no período {periodo}. "
    soma = float(serie.sum())
    # Série é recorte (top N): deixa explícito
    if len(serie) < total and soma < total - 0.5:
        return (
            abertura
            + f"No gráfico ({len(serie)} categorias): "
            + insight_top(serie, universo=total)
        )
    return abertura + insight_top(serie, universo=total)


def historia_tendencia(
    totais, mensal_lider: dict | None = None, universo: float | None = None
) -> str:
    """História de tendência: quem lidera no período e como o líder se move."""
    if totais is None or len(totais) == 0:
        return "Sem dados para este gráfico."
    base = insight_top(totais, universo=universo)
    if not mensal_lider:
        return base
    nome = mensal_lider.get("nome", "")
    ini, fim = mensal_lider.get("ini"), mensal_lider.get("fim")
    pico = mensal_lider.get("pico")
    n_ini, n_fim = mensal_lider.get("n_ini"), mensal_lider.get("n_fim")
    n_pico = mensal_lider.get("n_pico")
    if None in (ini, fim, n_ini, n_fim):
        return base
    if pico and n_pico is not None and pico not in {ini, fim}:
        return (
            f'{base} No tempo, "{nome}" parte de {n_br(n_ini)} em {ini}, '
            f"chega a {n_br(n_pico)} no pico ({pico}) e fecha em {n_br(n_fim)} em {fim}."
        )
    return (
        f'{base} No tempo, "{nome}" vai de {n_br(n_ini)} em {ini} '
        f"para {n_br(n_fim)} em {fim}."
    )


def historia_numerica(valores, sujeito: str, unidade: str = "") -> str:
    """História para histograma/série numérica (idade, semanas, peso)."""
    if valores is None or len(valores) == 0:
        return "Sem dados para este gráfico."
    serie = valores.dropna() if hasattr(valores, "dropna") else valores
    n = len(serie)
    if n == 0:
        return "Sem dados para este gráfico."
    med = float(serie.median())
    media = float(serie.mean())
    minimo, maximo = float(serie.min()), float(serie.max())
    uni = f" {unidade}" if unidade else ""
    return (
        f"Há {n_br(n)} {sujeito}. "
        f"A mediana fica em {_num(med)}{uni}, a média em {_num(media)}{uni}, "
        f"com valores de {_num(minimo)} a {_num(maximo)}{uni}."
    )


def historia_idades_por_grupo(grupos: dict, total: int, contexto: str) -> str:
    """Compara medianas de idade entre locais/grupos (só os do gráfico)."""
    if not grupos:
        return "Sem dados para este gráfico."
    medianas = {nome: float(vals.median()) for nome, vals in grupos.items() if len(vals)}
    if not medianas:
        return "Sem dados para este gráfico."
    jovem = min(medianas, key=medianas.get)
    velho = max(medianas, key=medianas.get)
    trechos = ", ".join(
        f'"{nome}" ({_num(med)} anos)'
        for nome, med in sorted(medianas.items(), key=lambda x: x[1])
    )
    return (
        f"{contexto} há {n_br(total)} registros com idade. "
        f"A mediana é menor em {jovem} ({_num(medianas[jovem])} anos) "
        f"e maior em {velho} ({_num(medianas[velho])} anos). "
        f"Medianas por grupo: {trechos}."
    )


def historia_cruzamento(tabela, eixo_x: str = "categoria", eixo_y: str = "grupo") -> str:
    """História para tabela cruzada / heatmap (dados exatos da figura)."""
    if tabela is None or getattr(tabela, "empty", True):
        return "Sem dados para este gráfico."
    total = int(tabela.values.sum())
    if total <= 0:
        return "Sem dados para este gráfico."
    emp = tabela.stack()
    celula = emp.idxmax()
    n_cel = int(emp.max())
    p_cel = 100 * n_cel / total
    totais_linha = tabela.sum(axis=1).sort_values(ascending=False)
    lider = str(totais_linha.index[0])
    p_lider = 100 * totais_linha.iloc[0] / total
    return (
        f"O cruzamento tem {n_br(total)} registros. "
        f'"{lider}" concentra {pct_br(p_lider)}% no eixo de {eixo_x}. '
        f'A combinação mais frequente é "{celula[0]}" × "{celula[1]}" '
        f"({n_br(n_cel)}; {pct_br(p_cel)}%)."
    )


def historia_proporcao(tabela_pct, contexto: str) -> str:
    """História para barras empilhadas em % (linhas = 100%)."""
    if tabela_pct is None or getattr(tabela_pct, "empty", True):
        return "Sem dados para este gráfico."
    emp = tabela_pct.stack()
    (linha, col), valor = emp.idxmax(), float(emp.max())
    return (
        f"{contexto} "
        f'Em "{linha}", "{col}" chega a {pct_br(valor)}% — '
        f"o maior peso relativo deste recorte."
    )


def historia_janela_ranking(
    ranking_completo,
    janela,
    nome: str,
    unidade: str,
) -> str:
    """Texto alinhado a gráfico que mostra só a vizinhança de um município."""
    if nome not in ranking_completo.index:
        return f"{nome} não entrou no ranking (faltou população de referência)."
    lugar = list(ranking_completo.index).index(nome) + 1
    valor = float(ranking_completo.loc[nome])
    lider_geral = ranking_completo.index[0]
    topo_geral = float(ranking_completo.iloc[0])
    lider_janela = janela.idxmax()
    topo_janela = float(janela.max())
    return (
        f"{nome} está na {lugar}ª posição de {n_br(len(ranking_completo))} municípios "
        f"({_num(valor)} {unidade}). "
        f'No ranking completo, o 1º lugar é "{lider_geral}" ({_num(topo_geral)}). '
        f"O gráfico mostra a vizinhança de {nome}: neste recorte, "
        f'"{lider_janela}" tem a maior taxa ({_num(topo_janela)}).'
    )


def vazio(msg: str = "Sem dados para este gráfico."):
    """Par (figura, recado) quando não há o que plotar."""
    return None, msg


def n_br(valor) -> str:
    """Número com ponto de milhar (pt-BR)."""
    return f"{int(valor):,}".replace(",", ".")


def pct_br(valor: float) -> str:
    """Percentual com uma casa e vírgula."""
    return f"{valor:.1f}".replace(".", ",")


def _num(valor: float) -> str:
    """Número decimal com vírgula (pt-BR), sem casas se for inteiro."""
    if abs(valor - round(valor)) < 1e-9:
        return n_br(round(valor))
    return f"{valor:.1f}".replace(".", ",")


def _extenso(n: int) -> str:
    """1/2/3 por extenso para o texto fluir melhor."""
    return {1: "primeiro", 2: "dois", 3: "três"}.get(n, str(n))
