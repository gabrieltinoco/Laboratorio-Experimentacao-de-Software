"""Testes gerais de execução e reprodutibilidade das simulações do Lab04."""

import numpy as np
import pandas as pd

from src.experimentos import TESTES, rodar_grade, rodar_todas
from src.simulacao import gerar_dados

PARAMETROS = {"mediana": 55.7, "sigma": 2.23}


def _gerar_normal(n, mediana, sigma, efeito, rng, n_rep=1):
    """Gera dois grupos normais idênticos sob H0 (efeito zero)."""
    sem_bot = rng.normal(mediana, sigma, size=(n_rep, n))
    com_bot = rng.normal(mediana * (1 - efeito), sigma, size=(n_rep, n))
    return sem_bot, com_bot


def test_erro_tipo_i_com_dados_normais_fica_entre_quatro_e_seis_por_cento():
    resultados = rodar_grade(
        geradores={"normal": _gerar_normal},
        testes=TESTES,
        efeitos=[0.0],
        n=30,
        rng=np.random.default_rng(42),
        n_rep=10_000,
        alpha=0.05,
        pergunta="Q1",
        params={"mediana": 0.0, "sigma": 1.0},
    )

    assert set(resultados["teste"]) == set(TESTES)
    assert resultados["taxa_rejeicao"].between(0.04, 0.06).all()


def test_mesma_semente_produz_resultados_identicos():
    def executar():
        return rodar_todas(
            np.random.default_rng(42),
            n_rep=250,
            efeitos=[0.0, 0.5],
            params=PARAMETROS,
        )

    pd.testing.assert_frame_equal(executar(), executar())


def test_gerar_dados_retorna_shape_repeticoes_por_observacoes():
    sem_bot, com_bot = gerar_dados(
        n=17,
        mediana=PARAMETROS["mediana"],
        sigma=PARAMETROS["sigma"],
        efeito=0.3,
        rng=np.random.default_rng(42),
        n_rep=5,
    )

    assert sem_bot.shape == (5, 17)
    assert com_bot.shape == (5, 17)
