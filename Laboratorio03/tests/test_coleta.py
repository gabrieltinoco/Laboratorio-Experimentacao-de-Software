"""Testes do critério de inclusão e persistência dos dados coletados."""

from __future__ import annotations

import json

from pipeline.coleta import ColetorRepositorio
from pipeline.http_client import ErroGitHub, Resposta


def release(identificador, dia, *, prerelease=False):
    return {
        "id": identificador,
        "tag_name": f"v{identificador}",
        "draft": False,
        "prerelease": prerelease,
        "published_at": f"2025-10-{dia:02}T00:00:00Z",
        "created_at": f"2025-10-{dia:02}T00:00:00Z",
        "html_url": "",
        "name": "",
        "body": "",
    }


def workflow_run(identificador, conclusion):
    return {
        "id": identificador,
        "name": "CI",
        "workflow_id": 1,
        "head_branch": "main",
        "head_sha": "abc",
        "event": "push",
        "status": "completed",
        "conclusion": conclusion,
        "created_at": "2025-10-10T00:00:00Z",
        "run_started_at": "2025-10-10T00:00:00Z",
        "updated_at": "2025-10-10T00:01:00Z",
        "html_url": "",
    }


class ClienteColeta:
    per_page = 100

    def __init__(self, releases, runs, comparacoes=None):
        self.releases = releases
        self.runs = runs
        self.comparacoes = comparacoes or {}

    def get_todos(self, caminho, params=None, chave=None):
        if caminho.endswith("/releases"):
            return self.releases
        resultado = self.comparacoes[caminho]
        if isinstance(resultado, Exception):
            raise resultado
        return resultado

    def paginas(self, caminho, params):
        yield Resposta(
            200,
            caminho,
            {"total_count": len(self.runs), "workflow_runs": self.runs},
        )


def config():
    return {
        "janela": {"inicio": "2025-10-01", "fim": "2025-10-31"},
        "inclusao": {"min_releases": 5, "min_workflow_runs": 3},
    }


def test_criterio_aplica_minimos_excluindo_prerelease_e_run_cancelado():
    cliente = ClienteColeta(
        [release(i, i, prerelease=(i == 5)) for i in range(1, 6)],
        [
            workflow_run(1, "success"),
            workflow_run(2, "failure"),
            workflow_run(3, "cancelled"),
        ],
    )
    coletor = ColetorRepositorio(config())

    motivo = coletor(cliente, {"repositorio": "o/r", "default_branch": "main"})

    assert motivo == "4 releases válidas (mínimo 5); 2 workflow runs válidos (mínimo 3)"
    assert coletor.coletas == {}


def test_coletor_guarda_dados_de_repo_aprovado_e_salva_jsonl(tmp_path):
    releases = [release(i, i) for i in range(1, 6)]
    comparacoes = {
        f"/repos/o/r/compare/v{i}...v{i + 1}": []
        for i in range(1, 5)
    }
    comparacoes["/repos/o/r/compare/v1...v2"] = ErroGitHub(404, "url")
    cliente = ClienteColeta(
        releases,
        [
            workflow_run(1, "success"),
            workflow_run(2, "failure"),
            workflow_run(3, "timed_out"),
            workflow_run(4, "cancelled"),
        ],
        comparacoes,
    )
    coletor = ColetorRepositorio(config())

    assert coletor(cliente, {"repositorio": "o/r", "default_branch": "main"}) is None
    coletor.salvar(tmp_path)

    assert len((tmp_path / "releases.jsonl").read_text(encoding="utf-8").splitlines()) == 5
    assert len((tmp_path / "commits_entre_releases.jsonl").read_text(encoding="utf-8").splitlines()) == 3
    assert len((tmp_path / "compare_404.jsonl").read_text(encoding="utf-8").splitlines()) == 1
    runs_salvos = [
        json.loads(linha)
        for linha in (tmp_path / "workflow_runs.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert len(runs_salvos) == 4
    resumo = json.loads((tmp_path / "coleta_resumo.json").read_text(encoding="utf-8"))
    assert resumo["o/r"]["meses_no_teto"] == []
    assert resumo["o/r"]["compare_404"] == 1
    assert resumo["o/r"]["workflow_runs_validas"] == 3
