"""Variantes de lead time: por release e por commit, em dias."""

from __future__ import annotations

from datetime import datetime
from statistics import median


def _instante(valor: str) -> datetime:
    return datetime.fromisoformat(valor.replace("Z", "+00:00"))


def _dias(release: dict, commit: dict) -> float | None:
    data_release = release.get("published_at")
    data_commit = commit.get("author_date")
    if not data_release or not data_commit:
        return None
    return (_instante(data_release) - _instante(data_commit)).total_seconds() / 86400


def lead_time_por_release(comparacoes: list[dict]) -> float | None:
    """Mediana do tempo entre o commit mais antigo de cada release e sua publicação."""
    valores = []
    for comparacao in comparacoes:
        duracoes = [
            valor
            for commit in comparacao.get("commits", [])
            if (valor := _dias(comparacao, commit)) is not None
        ]
        if duracoes:
            valores.append(max(duracoes))
    return median(valores) if valores else None


def lead_time_por_commit(comparacoes: list[dict]) -> float | None:
    """Mediana do tempo de cada commit até a publicação de sua release."""
    valores = [
        valor
        for comparacao in comparacoes
        for commit in comparacao.get("commits", [])
        if (valor := _dias(comparacao, commit)) is not None
    ]
    return median(valores) if valores else None
