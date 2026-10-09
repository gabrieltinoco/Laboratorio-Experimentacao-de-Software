"""Coleta de execuções de workflows, segmentada por mês para respeitar o teto da API."""

from __future__ import annotations

import calendar
import logging
from dataclasses import dataclass
from datetime import date

from pipeline.http_client import GitHubClient

log = logging.getLogger(__name__)
TETO_RUNS_POR_CONSULTA = 1000
PAGINAS_POR_CONSULTA = 10


@dataclass
class ColetaWorkflowRuns:
    runs: list[dict]
    totais_por_mes: dict[str, int]
    meses_no_teto: list[str]


def intervalos_mensais(inicio: str | date, fim: str | date) -> list[tuple[date, date]]:
    """Divide uma janela inclusiva em meses, preservando datas parciais nas pontas."""
    inicio = date.fromisoformat(inicio) if isinstance(inicio, str) else inicio
    fim = date.fromisoformat(fim) if isinstance(fim, str) else fim
    if fim < inicio:
        raise ValueError("O fim da janela deve ser igual ou posterior ao início.")

    intervalos = []
    ano, mes = inicio.year, inicio.month
    while (ano, mes) <= (fim.year, fim.month):
        primeiro = date(ano, mes, 1)
        ultimo = date(ano, mes, calendar.monthrange(ano, mes)[1])
        intervalos.append((max(inicio, primeiro), min(fim, ultimo)))
        if mes == 12:
            ano, mes = ano + 1, 1
        else:
            mes += 1
    return intervalos


def _normalizar_run(run: dict) -> dict:
    return {
        "id": run.get("id"),
        "name": run.get("name"),
        "workflow_id": run.get("workflow_id"),
        "head_branch": run.get("head_branch"),
        "head_sha": run.get("head_sha"),
        "event": run.get("event"),
        "status": run.get("status"),
        "conclusion": run.get("conclusion"),
        "created_at": run.get("created_at"),
        "run_started_at": run.get("run_started_at"),
        "updated_at": run.get("updated_at"),
        "html_url": run.get("html_url"),
    }


def coletar_workflow_runs(
    cliente: GitHubClient,
    repositorio: str,
    branch: str,
    inicio: str | date,
    fim: str | date,
) -> ColetaWorkflowRuns:
    """Coleta runs do branch padrão disparados por push, consultando um mês por vez."""
    runs: list[dict] = []
    totais: dict[str, int] = {}
    meses_no_teto: list[str] = []
    vistos: set[int | str] = set()

    for primeiro, ultimo in intervalos_mensais(inicio, fim):
        chave_mes = primeiro.strftime("%Y-%m")
        params = {
            "branch": branch,
            "event": "push",
            "created": f"{primeiro.isoformat()}..{ultimo.isoformat()}",
            "per_page": cliente.per_page,
        }
        total = 0
        coletadas_no_mes = 0
        for numero_pagina, pagina in enumerate(
            cliente.paginas(f"/repos/{repositorio}/actions/runs", params), start=1
        ):
            dados = pagina.dados
            total = int(dados.get("total_count", total))
            for run in dados.get("workflow_runs", []):
                item = _normalizar_run(run)
                identificador = item["id"]
                if identificador not in vistos:
                    runs.append(item)
                    vistos.add(identificador)
                    coletadas_no_mes += 1
            if numero_pagina >= PAGINAS_POR_CONSULTA:
                break

        totais[chave_mes] = total
        if total >= TETO_RUNS_POR_CONSULTA or coletadas_no_mes >= TETO_RUNS_POR_CONSULTA:
            meses_no_teto.append(chave_mes)
            log.warning(
                "%s teve %d workflow runs em %s; o teto da API pode truncar resultados.",
                repositorio,
                total,
                chave_mes,
            )

    return ColetaWorkflowRuns(runs, totais, meses_no_teto)
