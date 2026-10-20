"""Deployment rework rate (RQ 08): releases corretivas sobre o total de releases."""

from __future__ import annotations

from dataclasses import dataclass

from metricas.corretiva import classificar_comparacoes


@dataclass(frozen=True)
class ResumoRework:
    rework_rate: float | None
    releases_corretivas: int


def calcular_rework(comparacoes: list[dict], releases_na_janela: int) -> ResumoRework:
    """Releases sem compare (primeira da história ou 404) não podem ser corretivas,
    mas continuam no denominador, que é o total de releases principais da janela."""
    if releases_na_janela < 0:
        raise ValueError("O número de releases não pode ser negativo.")
    corretivas = sum(classificar_comparacoes(comparacoes).values())
    if corretivas > releases_na_janela:
        raise ValueError("Há mais releases corretivas que releases na janela.")
    return ResumoRework(
        rework_rate=corretivas / releases_na_janela if releases_na_janela else None,
        releases_corretivas=corretivas,
    )
