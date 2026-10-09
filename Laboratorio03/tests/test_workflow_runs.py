"""Testes de coleta mensal de workflow runs sem chamadas à API."""

from __future__ import annotations

import logging
from datetime import date

import pytest

from pipeline.http_client import Resposta
from pipeline.workflow_runs import coletar_workflow_runs, intervalos_mensais


def run(identificador, conclusao="success", **extras):
    return {
        "id": identificador,
        "name": "CI",
        "workflow_id": 10,
        "head_branch": "main",
        "head_sha": "abc",
        "event": "push",
        "status": "completed",
        "conclusion": conclusao,
        "created_at": "2025-10-15T10:00:00Z",
        "run_started_at": "2025-10-15T10:01:00Z",
        "updated_at": "2025-10-15T10:05:00Z",
        "html_url": "https://github.com/o/r/actions/runs/1",
        **extras,
    }


class ClienteRuns:
    per_page = 100

    def __init__(self, paginas_por_mes=None, total_por_mes=None):
        self.paginas_por_mes = paginas_por_mes or {}
        self.total_por_mes = total_por_mes or {}
        self.chamadas = []

    def paginas(self, caminho, params):
        self.chamadas.append((caminho, params))
        mes = params["created"][:7]
        paginas = self.paginas_por_mes.get(mes, [[]])
        for itens in paginas:
            yield Resposta(
                200,
                caminho,
                {"total_count": self.total_por_mes.get(mes, len(itens)), "workflow_runs": itens},
            )


def test_intervalos_mensais_preservam_janela_parcial():
    assert intervalos_mensais("2025-10-15", "2025-12-02") == [
        (date(2025, 10, 15), date(2025, 10, 31)),
        (date(2025, 11, 1), date(2025, 11, 30)),
        (date(2025, 12, 1), date(2025, 12, 2)),
    ]


def test_intervalos_mensais_rejeitam_janela_invertida():
    with pytest.raises(ValueError):
        intervalos_mensais("2025-11-01", "2025-10-31")


def test_coleta_filtra_por_parametros_padrao_e_registra_alerta(caplog):
    cliente = ClienteRuns(
        paginas_por_mes={
            "2025-10": [[run(1, "success"), run(2, "cancelled")]],
            "2025-11": [[run(3, "failure")]],
        },
        total_por_mes={"2025-10": 1000, "2025-11": 1},
    )
    with caplog.at_level(logging.WARNING):
        resultado = coletar_workflow_runs(cliente, "o/r", "main", "2025-10-15", "2025-11-03")

    assert [item["id"] for item in resultado.runs] == [1, 2, 3]
    assert resultado.totais_por_mes == {"2025-10": 1000, "2025-11": 1}
    assert resultado.meses_no_teto == ["2025-10"]
    assert len(cliente.chamadas) == 2
    assert all(params["branch"] == "main" for _, params in cliente.chamadas)
    assert all(params["event"] == "push" for _, params in cliente.chamadas)
    assert cliente.chamadas[0][1]["created"] == "2025-10-15..2025-10-31"
    assert "teto" in caplog.text


def test_coleta_para_na_decima_pagina_e_gera_alerta(caplog):
    paginas = [[run(indice)] for indice in range(10)]
    cliente = ClienteRuns(
        paginas_por_mes={"2025-10": paginas},
        total_por_mes={"2025-10": 1001},
    )
    with caplog.at_level(logging.WARNING):
        resultado = coletar_workflow_runs(cliente, "o/r", "main", "2025-10-01", "2025-10-31")

    assert len(resultado.runs) == 10
    assert resultado.meses_no_teto == ["2025-10"]
    assert len(cliente.chamadas) == 1
    assert "1001" in caplog.text
