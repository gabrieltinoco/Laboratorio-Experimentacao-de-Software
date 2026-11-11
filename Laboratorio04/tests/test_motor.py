"""Testes do motor de simulacao, das situacoes da Q3, da tabela dos dados reais
e da discussao do tamanho da amostra (frente do Integrante A).

Os testes automatizados gerais do projeto (S2-B3) ficam em test_experimentos.py.
"""

import numpy as np
import pandas as pd
import pytest

from src.cenarios_q3 import (
    SITUACOES,
    gerar_amostra_pequena,
    gerar_assimetria_extrema,
    gerar_com_outliers,
)
from src.dados_reais import resumo_grupos, tabela_testes_reais
from src.experimentos import (
    COLUNAS,
    TESTES,
    rodar_grade,
    rodar_todas,
    taxa_rejeicao,
)
from src.parametros import carregar_prs
from src.simulacao import gerar_dados
from src.estilo import COR_MW, COR_WELCH
from src.tamanho_amostra import (
    efeito_observado,
    grafico_tamanho_amostra,
    n_para_poder,
    poder_por_n,
)

PARAMS = {"mediana": 55.7, "sigma": 2.23}


# --------------------------------------------------------------- motor (S2-A1)


def test_taxa_rejeicao_fica_perto_de_alpha_sob_h0():
    rng = np.random.default_rng(1)
    taxa, inf, sup = taxa_rejeicao(
        gerar_dados, TESTES["mann_whitney"], efeito=0.0, n=30, rng=rng, n_rep=4000, **PARAMS
    )
    assert 0.035 < taxa < 0.065
    assert inf < taxa < sup


def test_taxa_rejeicao_cresce_com_o_efeito():
    rng = np.random.default_rng(2)
    for teste in TESTES.values():
        sem_efeito, _, _ = taxa_rejeicao(gerar_dados, teste, 0.0, 30, rng, n_rep=2000, **PARAMS)
        com_efeito, _, _ = taxa_rejeicao(gerar_dados, teste, 0.9, 30, rng, n_rep=2000, **PARAMS)
        assert com_efeito > sem_efeito + 0.2


def test_rodar_grade_devolve_formato_combinado():
    rng = np.random.default_rng(3)
    df = rodar_grade(
        {"base": gerar_dados}, TESTES, efeitos=[0.0, 0.5], n=12, rng=rng,
        n_rep=500, pergunta="Q2", params=PARAMS,
    )
    assert list(df.columns) == COLUNAS
    assert len(df) == 1 * 2 * 2
    assert set(df["teste"]) == {"welch", "mann_whitney"}
    assert (df["n_rep"] == 500).all()
    assert (df["n_por_grupo"] == 12).all()
    assert (df["pergunta"] == "Q2").all()
    assert ((df["ic95_inf"] <= df["taxa_rejeicao"]) & (df["taxa_rejeicao"] <= df["ic95_sup"])).all()


def test_rodar_grade_e_reproduzivel_com_a_mesma_semente():
    def rodar():
        return rodar_grade(
            {"base": gerar_dados}, TESTES, [0.0, 0.3], 10, np.random.default_rng(42),
            n_rep=300, pergunta="Q2", params=PARAMS,
        )

    pd.testing.assert_frame_equal(rodar(), rodar())


def test_rodar_grade_em_blocos_soma_todas_as_repeticoes():
    rng = np.random.default_rng(4)
    df = rodar_grade(
        {"base": gerar_dados}, TESTES, [0.0], 20, rng,
        n_rep=1000, pergunta="Q1", params=PARAMS, tamanho_bloco=130,
    )
    assert (df["n_rep"] == 1000).all()
    assert df["taxa_rejeicao"].between(0, 1).all()


def test_rodar_todas_cobre_q1_q2_e_as_tres_situacoes_da_q3():
    df = rodar_todas(np.random.default_rng(5), n_rep=200, efeitos=[0.0, 0.5], params=PARAMS)
    assert set(df["pergunta"]) == {"Q1", "Q2", "Q3"}
    q3 = df[df["pergunta"] == "Q3"]
    assert set(q3["situacao"]) == set(SITUACOES)
    assert len(q3) == len(SITUACOES) * 2 * 2
    assert (df.loc[df["pergunta"] == "Q1", "efeito"] == 0).all()
    assert q3.loc[q3["situacao"] == "amostra_pequena", "n_por_grupo"].eq(10).all()


# --------------------------------------------------------- situacoes (S2-A4)


@pytest.mark.parametrize(
    "gerador", [gerar_assimetria_extrema, gerar_com_outliers, gerar_amostra_pequena]
)
def test_geradores_q3_tem_a_assinatura_do_gerador_base(gerador):
    a, b = gerador(n=15, efeito=0.2, rng=np.random.default_rng(6), n_rep=4, **PARAMS)
    assert a.shape == (4, 15) and b.shape == (4, 15)
    assert (a > 0).all() and (b > 0).all()


def test_assimetria_extrema_dobra_o_sigma():
    a, _ = gerar_assimetria_extrema(
        n=20000, mediana=10.0, sigma=0.5, efeito=0.0, rng=np.random.default_rng(7)
    )
    assert np.log(a).std() == pytest.approx(1.0, rel=0.03)


def test_com_outliers_multiplica_cerca_de_5_por_cento_por_10():
    a, b = gerar_com_outliers(
        n=20000, mediana=1.0, sigma=0.01, efeito=0.0, rng=np.random.default_rng(8)
    )
    for x in (a, b):
        assert np.mean(x > 5) == pytest.approx(0.05, abs=0.006)


def test_amostra_pequena_usa_n_10():
    assert SITUACOES["amostra_pequena"]["n"] == 10
    assert SITUACOES["assimetria_extrema"]["n"] == 30


# ---------------------------------------------------- dados reais (F-A1)


def test_tabela_testes_reais_tem_uma_linha_por_teste():
    tabela = tabela_testes_reais(carregar_prs())
    assert list(tabela["teste"]) == ["welch", "mann_whitney"]
    assert {"estatistica", "p_valor", "efeito", "conclusao"} <= set(tabela.columns)
    assert tabela["p_valor"].between(0, 1).all()
    assert tabela["conclusao"].isin(["Rejeita H0", "Não rejeita H0"]).all()


def test_resumo_grupos_traz_mediana_e_media_reais():
    resumo = resumo_grupos(carregar_prs())
    assert resumo.loc["com_bot", "n"] == 30
    assert resumo.loc["com_bot", "mediana"] == pytest.approx(37.12, abs=0.01)
    assert resumo.loc["sem_bot", "media"] == pytest.approx(332.20, abs=0.01)


# ---------------------------------------------- tamanho da amostra (F-A3)


def test_efeito_observado_vem_das_medianas_ajustadas():
    assert efeito_observado(carregar_prs()) == pytest.approx(1 - 41.400 / 55.705, abs=0.001)


def test_poder_por_n_cresce_com_n():
    df = poder_por_n(np.random.default_rng(9), efeito=0.5, ns=[10, 200], n_rep=600, params=PARAMS)
    assert set(df["teste"]) == {"welch", "mann_whitney"}
    mw = df[df["teste"] == "mann_whitney"].set_index("n_por_grupo")["taxa_rejeicao"]
    assert mw.loc[200] > mw.loc[10]


def test_n_para_poder_interpola_o_cruzamento_de_80_por_cento():
    df = pd.DataFrame(
        {
            "teste": ["mann_whitney"] * 3 + ["welch"] * 3,
            "n_por_grupo": [100, 200, 400] * 2,
            "taxa_rejeicao": [0.5, 0.7, 0.9, 0.1, 0.2, 0.3],
        }
    )
    assert n_para_poder(df, "mann_whitney") == pytest.approx(300)
    assert n_para_poder(df, "welch") is None


def test_grafico_tamanho_amostra_usa_as_cores_dos_testes():
    df = pd.DataFrame(
        {
            "teste": ["mann_whitney", "mann_whitney", "welch", "welch"],
            "n_por_grupo": [30, 60, 30, 60],
            "taxa_rejeicao": [0.1, 0.3, 0.05, 0.1],
            "ic95_inf": [0.09, 0.29, 0.04, 0.09],
            "ic95_sup": [0.11, 0.31, 0.06, 0.11],
        }
    )
    fig = grafico_tamanho_amostra(df)
    cores = {t.name: t.line.color for t in fig.data}
    assert cores == {"Mann-Whitney": COR_MW, "t de Welch": COR_WELCH}
    assert any(s.y0 == 0.8 for s in fig.layout.shapes)
    assert fig.layout.xaxis.title.text and fig.layout.yaxis.title.text
