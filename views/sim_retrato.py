"""Retrato da mortalidade no município — gráficos do notebook."""

from charts import sim_cruzamentos as cruzamentos
from charts import sim_perfil as perfil
from charts import sim_territorio as territorio
from views.common import load_or_stop, periodo
from views.sim_tema import cabecalho, secao


def render() -> None:
    """Página completa do Retrato, em seções curtas."""
    df = load_or_stop()
    periodo_txt = periodo(df)
    cabecalho(
        "Retrato da mortalidade no município",
        f"Residentes de Araranguá · {periodo_txt} · {len(df)} óbitos",
        total_descobertas=13,
    )
    _perfil(df, periodo_txt)
    _cruzamentos(df, periodo_txt)
    _territorio(df, periodo_txt)


def _perfil(df, periodo_txt: str) -> None:
    """Distribuições simples (tempo, idade, sexo, causa)."""
    secao(
        "Perfil dos óbitos",
        perfil.obitos_por_ano(df, periodo_txt),
        perfil.media_por_mes(df, periodo_txt),
        perfil.obitos_por_faixa(df, periodo_txt),
        perfil.obitos_por_sexo(df, periodo_txt),
        perfil.obitos_por_raca(df, periodo_txt),
        perfil.obitos_por_escolaridade(df, periodo_txt),
        perfil.obitos_por_local(df, periodo_txt),
        perfil.top_causas(df, periodo_txt),
    )


def _cruzamentos(df, periodo_txt: str) -> None:
    """Ocupação e cruzamentos essenciais — A9 removido conforme revisão."""
    secao(
        "Cruzamentos",
        cruzamentos.top_ocupacoes(df, periodo_txt),
        cruzamentos.sexo_por_local(df, periodo_txt),
        cruzamentos.causas_por_faixa(df, periodo_txt),
    )


def _territorio(df, periodo_txt: str) -> None:
    """Comparação com SC e município de ocorrência — A13 removido."""
    ano_min, ano_max = int(df["ANO_OBITO"].min()), int(df["ANO_OBITO"].max())
    secao(
        "Território",
        territorio.ranking_taxa(ano_min, ano_max, periodo_txt),
        territorio.ocorrencia_por_municipio(df, periodo_txt),
    )
