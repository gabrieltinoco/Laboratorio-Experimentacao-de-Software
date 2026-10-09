"""Calculo das metricas DORA de cada repositorio coletado e montagem de repositorios.csv."""

from __future__ import annotations

import pandas as pd

from metricas.cfr import change_failure_rate, classificar_conclusion
from metricas.classificacao import (
    classificar_cfr,
    classificar_frequencia,
    classificar_geral,
    classificar_lead_time,
    classificar_recuperacao,
)
from metricas.deploy_freq import deployment_frequency
from metricas.lead_time import lead_time_por_commit, lead_time_por_release
from metricas.recuperacao import calcular_recuperacao


def _classificar(classificador, valor: float | None) -> str | None:
    return None if valor is None else classificador(valor)


def metricas_do_repositorio(coleta: dict, inicio: str, fim: str) -> dict:
    """Metricas e classificacao DORA de referencia (C1: release, lead time (a), CFR (a))."""
    runs = coleta["workflow_runs"]
    recuperacao = calcular_recuperacao(runs, fim)
    frequencia = deployment_frequency(coleta["releases"], inicio, fim)
    lead_time_a = lead_time_por_release(coleta["comparacoes"])
    cfr_a = change_failure_rate(runs)

    categorias = {
        "categoria_frequencia": classificar_frequencia(frequencia),
        "categoria_lead_time": _classificar(classificar_lead_time, lead_time_a),
        "categoria_cfr": _classificar(classificar_cfr, cfr_a),
        "categoria_recuperacao": _classificar(classificar_recuperacao, recuperacao.mediana_horas),
    }
    # Sem as quatro metricas a mediana dos pontos mudaria de significado.
    geral = None if None in categorias.values() else classificar_geral(list(categorias.values()))

    return {
        "releases_na_janela": sum(
            not r["draft"] and not r["prerelease"] and bool(r["published_at"])
            and inicio <= r["published_at"][:10] <= fim
            for r in coleta["releases"]
        ),
        "releases_comparadas": len(coleta["comparacoes"]),
        "compare_404": len(coleta["compare_404"]),
        "workflow_runs_validos": sum(classificar_conclusion(r["conclusion"]) != "ignorar" for r in runs),
        "meses_no_teto_de_runs": len(coleta["meses_no_teto"]),
        "deploy_freq_semana": frequencia,
        "lead_time_release_dias": lead_time_a,
        "lead_time_commit_dias": lead_time_por_commit(coleta["comparacoes"]),
        "cfr_ci": cfr_a,
        "recuperacao_horas": recuperacao.mediana_horas,
        "episodios_falha": len(recuperacao.episodios),
        "episodios_censurados": recuperacao.censurados,
        "proporcao_censurados": recuperacao.proporcao_censurados,
        **categorias,
        "categoria_geral": geral,
    }


def consolidar(amostra: pd.DataFrame, coletas: dict[str, dict], inicio: str, fim: str) -> pd.DataFrame:
    """Uma linha por repositorio da amostra: metadados seguidos das metricas."""
    if amostra.empty:
        return amostra
    metricas = pd.DataFrame([
        {"repositorio": nome, **metricas_do_repositorio(coletas[nome], inicio, fim)}
        for nome in amostra["repositorio"]
    ])
    return amostra.merge(metricas, on="repositorio").sort_values("repositorio", ignore_index=True)
