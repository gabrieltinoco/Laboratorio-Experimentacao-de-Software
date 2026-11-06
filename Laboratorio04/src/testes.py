"""Testes estatísticos vetorizados para os dados do Lab04."""

from __future__ import annotations

from typing import TypedDict

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy import stats
from scipy.special import gammaln

Resultado = float | NDArray[np.float64]


class ResultadoTeste(TypedDict):
    estatistica: Resultado
    p_valor: Resultado
    efeito: Resultado


def _validar_amostras(a: ArrayLike, b: ArrayLike) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    grupo_a = np.asarray(a, dtype=float)
    grupo_b = np.asarray(b, dtype=float)
    if grupo_a.ndim < 1 or grupo_b.ndim < 1:
        raise ValueError("cada grupo deve ter ao menos uma dimensão")
    if grupo_a.shape[-1] < 2 or grupo_b.shape[-1] < 2:
        raise ValueError("cada grupo deve conter ao menos duas observações")
    if grupo_a.shape[:-1] != grupo_b.shape[:-1]:
        raise ValueError("os grupos devem ter as mesmas dimensões antes do eixo das observações")
    if not np.isfinite(grupo_a).all() or not np.isfinite(grupo_b).all():
        raise ValueError("os grupos devem conter apenas valores finitos")
    return grupo_a, grupo_b


def _normalizar_saida(valor: ArrayLike) -> Resultado:
    resultado = np.asarray(valor, dtype=float)
    if not np.isfinite(resultado).all():
        raise FloatingPointError("o teste produziu um resultado não finito")
    if resultado.ndim == 0:
        return float(resultado)
    return resultado


def teste_welch(a: ArrayLike, b: ArrayLike) -> ResultadoTeste:
    """Aplica o t de Welch e retorna Hedges' g (eixo das observações: -1)."""
    grupo_a, grupo_b = _validar_amostras(a, b)
    n_a = grupo_a.shape[-1]
    n_b = grupo_b.shape[-1]
    graus_liberdade_pooled = n_a + n_b - 2
    variancia_a = np.var(grupo_a, axis=-1, ddof=1)
    variancia_b = np.var(grupo_b, axis=-1, ddof=1)
    variancia_pooled = (
        (n_a - 1) * variancia_a + (n_b - 1) * variancia_b
    ) / graus_liberdade_pooled
    if np.any(variancia_pooled <= 0):
        raise ValueError("Hedges' g não é definido para grupos constantes")

    resultado = stats.ttest_ind(
        grupo_a,
        grupo_b,
        equal_var=False,
        axis=-1,
        alternative="two-sided",
    )
    diferenca_padronizada = (
        np.mean(grupo_a, axis=-1) - np.mean(grupo_b, axis=-1)
    ) / np.sqrt(variancia_pooled)
    correcao_pequena_amostra = np.exp(
        gammaln(graus_liberdade_pooled / 2)
        - gammaln((graus_liberdade_pooled - 1) / 2)
        - 0.5 * np.log(graus_liberdade_pooled / 2)
    )
    return {
        "estatistica": _normalizar_saida(resultado.statistic),
        "p_valor": _normalizar_saida(resultado.pvalue),
        "efeito": _normalizar_saida(diferenca_padronizada * correcao_pequena_amostra),
    }


def teste_mann_whitney(a: ArrayLike, b: ArrayLike) -> ResultadoTeste:
    """Aplica Mann-Whitney e retorna r bisserial por postos (eixo -1)."""
    grupo_a, grupo_b = _validar_amostras(a, b)
    resultado = stats.mannwhitneyu(
        grupo_a,
        grupo_b,
        alternative="two-sided",
        axis=-1,
        method="asymptotic",
    )
    n_a = grupo_a.shape[-1]
    n_b = grupo_b.shape[-1]
    efeito = 1 - 2 * np.asarray(resultado.statistic, dtype=float) / (n_a * n_b)
    return {
        "estatistica": _normalizar_saida(resultado.statistic),
        "p_valor": _normalizar_saida(resultado.pvalue),
        "efeito": _normalizar_saida(efeito),
    }
