"""Orquestra a coleta por repositório e aplica os critérios mínimos do enunciado."""

from __future__ import annotations

import json
from pathlib import Path

from metricas.cfr import classificar_conclusion
from pipeline.http_client import GitHubClient
from pipeline.releases import coletar_commits_entre_releases, coletar_releases
from pipeline.workflow_runs import coletar_workflow_runs


class ColetorRepositorio:
    """Callable usado como etapa de seleção; mantém os dados dos aprovados."""

    def __init__(self, config: dict):
        self.inicio = config["janela"]["inicio"]
        self.fim = config["janela"]["fim"]
        self.min_releases = int(config["inclusao"]["min_releases"])
        self.min_runs = int(config["inclusao"]["min_workflow_runs"])
        self.coletas: dict[str, dict] = {}

    def __call__(self, cliente: GitHubClient, metadados: dict) -> str | None:
        repositorio = metadados["repositorio"]
        releases = coletar_releases(cliente, repositorio, self.inicio, self.fim)
        workflow_runs = coletar_workflow_runs(
            cliente,
            repositorio,
            metadados["default_branch"],
            self.inicio,
            self.fim,
        )

        validas = [
            release for release in releases
            if not release["draft"]
            and not release["prerelease"]
            and release["published_at"]
            and self.inicio <= release["published_at"][:10] <= self.fim
        ]
        runs_validas = [
            run for run in workflow_runs.runs
            if classificar_conclusion(run["conclusion"]) != "ignorar"
        ]

        motivos = []
        if len(validas) < self.min_releases:
            motivos.append(f"{len(validas)} releases válidas (mínimo {self.min_releases})")
        if len(runs_validas) < self.min_runs:
            motivos.append(f"{len(runs_validas)} workflow runs válidos (mínimo {self.min_runs})")
        if motivos:
            return "; ".join(motivos)

        comparacoes, ignoradas_404 = coletar_commits_entre_releases(
            cliente, repositorio, releases, self.inicio, self.fim
        )
        self.coletas[repositorio] = {
            "releases": releases,
            "comparacoes": comparacoes,
            "compare_404": ignoradas_404,
            "workflow_runs": workflow_runs.runs,
            "workflow_runs_por_mes": workflow_runs.totais_por_mes,
            "meses_no_teto": workflow_runs.meses_no_teto,
        }
        return None

    def salvar(self, diretorio: str | Path) -> None:
        """Salva a coleta aprovada em JSONL, um registro por linha, para integração."""
        diretorio = Path(diretorio)
        diretorio.mkdir(parents=True, exist_ok=True)
        registros = {
            "releases.jsonl": "releases",
            "commits_entre_releases.jsonl": "comparacoes",
            "compare_404.jsonl": "compare_404",
            "workflow_runs.jsonl": "workflow_runs",
        }
        for nome_arquivo, chave in registros.items():
            arquivo = diretorio / nome_arquivo
            with arquivo.open("w", encoding="utf-8", newline="\n") as saida:
                for repositorio, coleta in sorted(self.coletas.items()):
                    for item in coleta[chave]:
                        saida.write(
                            json.dumps(
                                {"repositorio": repositorio, **item},
                                ensure_ascii=False,
                                sort_keys=True,
                            )
                            + "\n"
                        )

        resumo = {
            repositorio: {
                "releases_validas_na_janela": sum(
                    not release["draft"]
                    and not release["prerelease"]
                    and release["published_at"]
                    and self.inicio <= release["published_at"][:10] <= self.fim
                    for release in coleta["releases"]
                ),
                "workflow_runs_coletadas": len(coleta["workflow_runs"]),
                "workflow_runs_validas": sum(
                    classificar_conclusion(run["conclusion"]) != "ignorar"
                    for run in coleta["workflow_runs"]
                ),
                "compare_404": len(coleta["compare_404"]),
                "workflow_runs_por_mes": coleta["workflow_runs_por_mes"],
                "meses_no_teto": coleta["meses_no_teto"],
            }
            for repositorio, coleta in sorted(self.coletas.items())
        }
        (diretorio / "coleta_resumo.json").write_text(
            json.dumps(resumo, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
