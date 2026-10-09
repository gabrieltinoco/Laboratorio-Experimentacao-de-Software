"""Classificação DORA de referência definida para o laboratório."""

from __future__ import annotations

from math import floor, isfinite
from statistics import median

CATEGORIAS = ("Elite", "High", "Medium", "Low")
PONTOS = {categoria: 4 - indice for indice, categoria in enumerate(CATEGORIAS)}


def _validar(valor: float) -> None:
    if not isfinite(valor) or valor < 0:
        raise ValueError("A métrica deve ser um número finito e não negativo.")


def classificar_frequencia(valor: float) -> str:
    _validar(valor)
    if valor >= 7:
        return "Elite"
    if valor >= 1:
        return "High"
    if valor >= 1 / 4.345:
        return "Medium"
    return "Low"


def classificar_lead_time(dias: float) -> str:
    _validar(dias)
    if dias < 1:
        return "Elite"
    if dias < 7:
        return "High"
    if dias < 30:
        return "Medium"
    return "Low"


def classificar_cfr(proporcao: float) -> str:
    _validar(proporcao)
    if proporcao > 1:
        raise ValueError("O CFR deve ser informado como proporção entre 0 e 1.")
    if proporcao <= 0.15:
        return "Elite"
    if proporcao <= 0.30:
        return "High"
    if proporcao <= 0.45:
        return "Medium"
    return "Low"


def classificar_recuperacao(horas: float) -> str:
    _validar(horas)
    if horas < 1:
        return "Elite"
    if horas < 24:
        return "High"
    if horas < 168:
        return "Medium"
    return "Low"


def classificar_geral(categorias: list[str]) -> str:
    """Mediana dos pontos das quatro métricas, arredondada para baixo."""
    if len(categorias) != 4 or any(categoria not in PONTOS for categoria in categorias):
        raise ValueError("A classificação geral requer quatro categorias DORA válidas.")
    nota = floor(median(PONTOS[categoria] for categoria in categorias))
    return CATEGORIAS[4 - nota]
