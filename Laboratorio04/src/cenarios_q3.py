"""Situacoes da Q3: geradores que violam os pressupostos do t de Welch.

Todos tem a mesma assinatura do gerador base (src.simulacao.gerar_dados):
    gerador(n, mediana, sigma, efeito, rng, n_rep=1) -> (sem_bot, com_bot)
com shape (n_rep, n). Com efeito = 0 os dois grupos continuam vindo da mesma
distribuicao, entao H0 segue verdadeira e a Q1 pode ser repetida em cada situacao.
"""

from __future__ import annotations

import numpy as np

from src.simulacao import gerar_dados

FRACAO_OUTLIERS = 0.05
FATOR_OUTLIERS = 10.0
N_PEQUENO = 10


def gerar_assimetria_extrema(n, mediana, sigma, efeito, rng, n_rep=1):
    """Lognormal com o sigma dobrado: cauda direita muito mais pesada."""
    return gerar_dados(n=n, mediana=mediana, sigma=2 * sigma, efeito=efeito, rng=rng, n_rep=n_rep)


def gerar_com_outliers(n, mediana, sigma, efeito, rng, n_rep=1):
    """Lognormal base em que cada valor tem 5% de chance de ser multiplicado por 10.

    A contaminacao e sorteada nos dois grupos da mesma forma (PRs esquecidos
    abertos por semanas aparecem com e sem bot).
    """
    a, b = gerar_dados(n=n, mediana=mediana, sigma=sigma, efeito=efeito, rng=rng, n_rep=n_rep)
    for x in (a, b):
        x[rng.random(x.shape) < FRACAO_OUTLIERS] *= FATOR_OUTLIERS
    return a, b


def gerar_amostra_pequena(n, mediana, sigma, efeito, rng, n_rep=1):
    """Mesmo gerador base; a situacao e definida por n = 10 em SITUACOES."""
    return gerar_dados(n=n, mediana=mediana, sigma=sigma, efeito=efeito, rng=rng, n_rep=n_rep)


SITUACOES = {
    "assimetria_extrema": {
        "gerador": gerar_assimetria_extrema,
        "n": 30,
        "descricao": "sigma × 2",
        "viola": (
            "Normalidade aproximada da média amostral: com cauda tão pesada, n = 30 "
            "não basta para o Teorema Central do Limite."
        ),
    },
    "com_outliers": {
        "gerador": gerar_com_outliers,
        "n": 30,
        "descricao": "5% dos valores × 10",
        "viola": (
            "Ausência de valores extremos: poucos outliers inflam a variância e "
            "dominam a média, que é o que o Welch compara."
        ),
    },
    "amostra_pequena": {
        "gerador": gerar_amostra_pequena,
        "n": N_PEQUENO,
        "descricao": "n = 10 por grupo",
        "viola": (
            "Amostra grande o bastante para a aproximação t: com n = 10 e dados "
            "assimétricos, a estatística t fica longe da t de Student."
        ),
    },
}
