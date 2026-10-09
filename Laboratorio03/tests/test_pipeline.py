"""Testes do pipeline completo (python -m pipeline) com um cliente falso (sem rede)."""

from __future__ import annotations

import json

import pandas as pd
import pytest
import yaml

import pipeline.__main__ as principal
from pipeline.consolidacao import consolidar, metricas_do_repositorio
from pipeline.http_client import Resposta
from pipeline.selecao import consulta_da_faixa

INICIO, FIM = "2025-10-01", "2026-09-30"
CONSULTA = consulta_da_faixa(1000, None, INICIO)


def item_busca(nome):
    return {"full_name": nome, "html_url": f"https://github.com/{nome}", "stargazers_count": 1500,
            "language": "Python", "default_branch": "main", "created_at": "2020-01-01T00:00:00Z"}


def release(tag, publicada):
    return {"id": tag, "tag_name": tag, "draft": False, "prerelease": False, "published_at": publicada,
            "created_at": publicada, "html_url": "", "name": tag, "body": ""}


def commit(data):
    return {"sha": data, "commit": {"author": {"date": data}, "message": "fix"}, "html_url": ""}


def run(identificador, inicio, fim, conclusion):
    return {"id": identificador, "name": "CI", "workflow_id": 1, "head_branch": "main", "head_sha": "x",
            "event": "push", "status": "completed", "conclusion": conclusion, "created_at": inicio,
            "run_started_at": inicio, "updated_at": fim, "html_url": ""}


# Exemplos do enunciado: v1.1 com lead time (a) de 13 dias e episodio de falha de 1h20.
RELEASES = {
    "o/bom": [
        release("v1.0", "2025-09-01T00:00:00Z"),
        release("v1.1", "2026-03-15T00:00:00Z"),
        release("v1.2", "2026-04-01T00:00:00Z"),
    ],
    "o/fraco": [release("v0.1", "2026-01-01T00:00:00Z")],
}
COMPARE = {
    "/repos/o/bom/compare/v1.0...v1.1": [
        commit("2026-03-02T00:00:00Z"), commit("2026-03-10T00:00:00Z"), commit("2026-03-14T00:00:00Z")],
    "/repos/o/bom/compare/v1.1...v1.2": [commit("2026-03-31T00:00:00Z")],
}
RUNS = {
    "o/bom": [
        run(1, "2026-01-10T09:00:00Z", "2026-01-10T09:05:00Z", "success"),
        run(2, "2026-01-10T10:00:00Z", "2026-01-10T10:05:00Z", "failure"),
        run(3, "2026-01-10T10:30:00Z", "2026-01-10T10:35:00Z", "failure"),
        run(4, "2026-01-10T11:00:00Z", "2026-01-10T11:05:00Z", "cancelled"),
        run(5, "2026-01-10T11:15:00Z", "2026-01-10T11:20:00Z", "success"),
    ],
    "o/fraco": [run(9, "2026-01-10T09:00:00Z", "2026-01-10T09:05:00Z", "success")],
}


class ClienteFalso:
    per_page = 100

    def paginas(self, caminho, params):
        if caminho == "/search/repositories":
            yield Resposta(200, caminho, {"total_count": 2, "items": [item_busca(n) for n in RELEASES]})
            return
        nome = caminho.removeprefix("/repos/").removesuffix("/actions/runs")
        de, ate = params["created"].split("..")
        runs = [r for r in RUNS[nome] if de <= r["created_at"][:10] <= ate]
        yield Resposta(200, caminho, {"total_count": len(runs), "workflow_runs": runs})

    def get(self, caminho, params=None):
        return Resposta(200, caminho, {"total_count": 1, "workflows": []})

    def contar(self, caminho, params=None):
        return 3

    def get_todos(self, caminho, params=None, chave=None):
        if caminho.endswith("/releases"):
            return RELEASES[caminho.removeprefix("/repos/").removesuffix("/releases")]
        return COMPARE[caminho]


def config(tmp_path):
    return {
        "janela": {"inicio": INICIO, "fim": FIM},
        "selecao": {"faixas_estrelas": [[1000, None]], "max_repositorios": 10, "semente": 42},
        "inclusao": {"min_releases": 2, "min_workflow_runs": 3},
        "caminhos": {"dados": str(tmp_path / "dados"), "cache": str(tmp_path / "cache")},
    }


def test_executar_calcula_metricas_e_aplica_criterio_de_inclusao(tmp_path):
    repositorios = principal.executar(config(tmp_path), ClienteFalso())

    assert list(repositorios["repositorio"]) == ["o/bom"]
    linha = repositorios.iloc[0]
    assert linha["releases_na_janela"] == 2
    assert linha["deploy_freq_semana"] == pytest.approx(2 / (365 / 7))
    assert linha["lead_time_release_dias"] == pytest.approx(7)   # mediana de 13 e 1
    assert linha["lead_time_commit_dias"] == pytest.approx(3)    # mediana de 13, 5, 1 e 1
    assert linha["workflow_runs_validos"] == 4
    assert linha["cfr_ci"] == pytest.approx(0.5)
    assert linha["recuperacao_horas"] == pytest.approx(4 / 3)
    assert linha["episodios_censurados"] == 0
    assert [linha[c] for c in ("categoria_frequencia", "categoria_lead_time", "categoria_cfr",
                               "categoria_recuperacao", "categoria_geral")] == [
        "Low", "Medium", "Low", "High", "Low"]
    assert linha["contribuidores"] == 3


def test_executar_grava_todas_as_saidas(tmp_path):
    principal.executar(config(tmp_path), ClienteFalso())
    dados = tmp_path / "dados"

    for arquivo in ("metadados.csv", "funil.csv", "descartes.csv", "repositorios.csv",
                    "releases.jsonl", "workflow_runs.jsonl", "coleta_resumo.json"):
        assert (dados / arquivo).exists(), arquivo
    descartes = pd.read_csv(dados / "descartes.csv")
    assert list(descartes["repositorio"]) == ["o/fraco"]
    assert descartes["etapa"].iloc[0] == principal.ETAPA_INCLUSAO
    assert list(json.loads((dados / "coleta_resumo.json").read_text(encoding="utf-8"))) == ["o/bom"]


def test_repositorio_sem_release_anterior_fica_sem_lead_time_e_sem_categoria_geral():
    coleta = {
        "releases": [release("v1.0", "2026-01-01T00:00:00Z")],
        "comparacoes": [],
        "compare_404": [],
        "workflow_runs": RUNS["o/bom"],
        "meses_no_teto": [],
    }
    metricas = metricas_do_repositorio(coleta, INICIO, FIM)

    assert metricas["lead_time_release_dias"] is None
    assert metricas["lead_time_commit_dias"] is None
    assert metricas["categoria_lead_time"] is None
    assert metricas["categoria_geral"] is None
    assert metricas["categoria_cfr"] == "Low"


def test_consolidar_amostra_vazia():
    assert consolidar(pd.DataFrame(), {}, INICIO, FIM).empty


def test_main_le_config_e_usa_cliente_do_config(tmp_path, monkeypatch):
    arquivo = tmp_path / "config.yaml"
    arquivo.write_text(yaml.safe_dump(config(tmp_path)), encoding="utf-8")
    monkeypatch.setattr(principal.GitHubClient, "from_config", classmethod(lambda cls, cfg: ClienteFalso()))

    principal.main(["--config", str(arquivo)])

    assert len(pd.read_csv(tmp_path / "dados" / "repositorios.csv")) == 1
