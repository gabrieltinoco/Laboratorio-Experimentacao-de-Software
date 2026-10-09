"""Deployment frequency em releases por semana."""

from __future__ import annotations

from datetime import date, datetime


def _data(valor: str) -> date:
    return datetime.fromisoformat(valor.replace("Z", "+00:00")).date()


def deployment_frequency(releases: list[dict], inicio: str | date, fim: str | date) -> float:
    """Conta releases publicadas (sem drafts/pré-releases) na janela, por semana."""
    inicio = date.fromisoformat(inicio) if isinstance(inicio, str) else inicio
    fim = date.fromisoformat(fim) if isinstance(fim, str) else fim
    if fim < inicio:
        raise ValueError("O fim da janela deve ser igual ou posterior ao início.")
    contagem = sum(
        not release.get("draft", False)
        and not release.get("prerelease", False)
        and bool(release.get("published_at"))
        and inicio <= _data(release["published_at"]) <= fim
        for release in releases
    )
    semanas = ((fim - inicio).days + 1) / 7
    return contagem / semanas
