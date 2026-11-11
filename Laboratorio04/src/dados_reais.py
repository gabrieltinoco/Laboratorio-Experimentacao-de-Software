"""Testes aplicados aos dados reais (secao 6 do dashboard).

Convencao: a = sem_bot, b = com_bot. Estatistica t > 0 e Hedges' g > 0
significam que a media sem bot e maior; r bisserial (1 - 2U/(n1*n2)) < 0
significa que os PRs sem bot tendem a demorar mais.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.estilo import NOMES_TESTE
from src.testes import teste_mann_whitney, teste_welch

ALPHA = 0.05
MEDIDA_EFEITO = {"welch": "Hedges' g", "mann_whitney": "r bisserial"}


def _grupos(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    sem = df.loc[df["grupo"] == "sem_bot", "horas_ate_merge"].to_numpy(dtype=float)
    com = df.loc[df["grupo"] == "com_bot", "horas_ate_merge"].to_numpy(dtype=float)
    return sem, com


def tabela_testes_reais(df: pd.DataFrame, alpha: float = ALPHA) -> pd.DataFrame:
    """Uma linha por teste: estatistica, p-valor, tamanho do efeito e conclusao."""
    sem, com = _grupos(df)
    linhas = []
    for nome, teste in (("welch", teste_welch), ("mann_whitney", teste_mann_whitney)):
        r = teste(sem, com)
        linhas.append(
            {
                "teste": nome,
                "nome": NOMES_TESTE[nome],
                "estatistica": float(r["estatistica"]),
                "p_valor": float(r["p_valor"]),
                "medida_efeito": MEDIDA_EFEITO[nome],
                "efeito": float(r["efeito"]),
                "conclusao": "Rejeita H0" if r["p_valor"] < alpha else "Não rejeita H0",
            }
        )
    return pd.DataFrame(linhas)


def resumo_grupos(df: pd.DataFrame) -> pd.DataFrame:
    """n, mediana, media, minimo e maximo das horas ate o merge, por grupo."""
    return (
        df.groupby("grupo")["horas_ate_merge"]
        .agg(n="size", mediana="median", media="mean", minimo="min", maximo="max")
        .reindex(["sem_bot", "com_bot"])
    )
