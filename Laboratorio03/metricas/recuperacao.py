"""Episódios de recuperação por workflow, incluindo episódios censurados."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from statistics import median

from metricas.cfr import classificar_conclusion


@dataclass(frozen=True)
class EpisodioRecuperacao:
    workflow_id: int | str | None
    inicio: str
    fim: str | None
    horas: float | None
    censurado: bool


@dataclass(frozen=True)
class ResumoRecuperacao:
    mediana_horas: float | None
    episodios: tuple[EpisodioRecuperacao, ...]
    censurados: int
    proporcao_censurados: float | None


def _instante(run: dict, campo: str) -> datetime:
    valor = run.get(campo)
    if not valor:
        raise ValueError(f"Workflow run sem timestamp obrigatório: {campo}")
    return datetime.fromisoformat(valor.replace("Z", "+00:00"))


def calcular_recuperacao(
    workflow_runs: list[dict], fim_janela: str | date | None = None
) -> ResumoRecuperacao:
    """Calcula mediana em horas e proporção de episódios censurados."""
    limite = date.fromisoformat(fim_janela) if isinstance(fim_janela, str) else fim_janela
    por_workflow: dict[int | str | None, list[dict]] = {}
    for run in workflow_runs:
        por_workflow.setdefault(run.get("workflow_id"), []).append(run)

    episodios: list[EpisodioRecuperacao] = []
    for workflow_id, runs in por_workflow.items():
        avaliaveis = [
            run for run in runs
            if classificar_conclusion(run.get("conclusion")) != "ignorar"
        ]
        if limite is not None:
            avaliaveis = [
                run for run in avaliaveis
                if _instante(run, "run_started_at").date() <= limite
                and _instante(run, "updated_at").date() <= limite
            ]
        ordenadas = sorted(avaliaveis, key=lambda run: _instante(run, "run_started_at"))
        houve_sucesso = False
        falha_ativa: dict | None = None
        for run in ordenadas:
            classificacao = classificar_conclusion(run.get("conclusion"))
            if classificacao == "sucesso":
                if falha_ativa is not None:
                    inicio = _instante(falha_ativa, "run_started_at")
                    fim = _instante(run, "updated_at")
                    episodios.append(
                        EpisodioRecuperacao(
                            workflow_id,
                            falha_ativa["run_started_at"],
                            run["updated_at"],
                            (fim - inicio).total_seconds() / 3600,
                            False,
                        )
                    )
                    falha_ativa = None
                houve_sucesso = True
            elif classificacao == "falha" and houve_sucesso and falha_ativa is None:
                falha_ativa = run

        if falha_ativa is not None:
            episodios.append(
                EpisodioRecuperacao(
                    workflow_id,
                    falha_ativa["run_started_at"],
                    None,
                    None,
                    True,
                )
            )

    duracoes = [episodio.horas for episodio in episodios if episodio.horas is not None]
    censurados = sum(episodio.censurado for episodio in episodios)
    proporcao = censurados / len(episodios) if episodios else None
    return ResumoRecuperacao(
        median(duracoes) if duracoes else None,
        tuple(episodios),
        censurados,
        proporcao,
    )
