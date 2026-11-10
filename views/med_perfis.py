"""Perfis de cuidado e tratamento na farmácia básica."""

from charts import med_destaques as graficos_destaques
from charts import med_perfis as graficos
from data.prepare_med import load_med, periodo_med
from views.common import exige
from views.sim_tema import cabecalho, secao


def render() -> None:
    """Página de perfis e destaques da Farmácia Básica (Card #16)."""
    df = exige(load_med, "Nenhuma dispensação encontrada.")
    periodo = periodo_med(df)
    cabecalho(
        "Quais perfis de cuidado e tratamento aparecem?",
        f"Farmácia Básica · {periodo} · {len(df):,} registros",
        "medicamentos",
        total_descobertas=4,
    )

    secao("Distribuição dos perfis", graficos.volume_por_perfil(df, periodo))
    secao(
        "Top 5 medicamentos por perfil",
        (None, "Escolha um grupo de cuidado para ver o Top 5 de medicamentos."),
        extra=lambda: graficos.top5_por_perfil_seletor(df, periodo),
    )
    secao("Top 10 geral", graficos_destaques.top_saidas(df, periodo))
    secao("Evolução mensal", graficos_destaques.sazonalidade_tipo(df, periodo))
