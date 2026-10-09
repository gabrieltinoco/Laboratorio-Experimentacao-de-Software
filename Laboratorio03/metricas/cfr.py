"""Classificação de conclusões de CI e change failure rate (proxy de CI)."""

from __future__ import annotations

CONCLUSOES_FALHA = {"failure", "timed_out", "startup_failure"}
CONCLUSOES_SUCESSO = {"success"}


def classificar_conclusion(conclusion: str | None) -> str:
    """Mapeia conclusions para sucesso, falha ou ignorar conforme o enunciado."""
    if conclusion in CONCLUSOES_SUCESSO:
        return "sucesso"
    if conclusion in CONCLUSOES_FALHA:
        return "falha"
    return "ignorar"


def change_failure_rate(workflow_runs: list[dict]) -> float | None:
    """Retorna falhas/(falhas+sucessos) como proporção, ou None sem casos válidos."""
    classificacoes = [classificar_conclusion(run.get("conclusion")) for run in workflow_runs]
    falhas = classificacoes.count("falha")
    avaliaveis = falhas + classificacoes.count("sucesso")
    return falhas / avaliaveis if avaliaveis else None
