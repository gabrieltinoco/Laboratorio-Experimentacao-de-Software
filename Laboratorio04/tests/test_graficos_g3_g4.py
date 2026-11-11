"""Testes dos graficos G3 (erro tipo I) e G4 (poder) lidos de results/q1_q2_q3.csv."""

import numpy as np
import pandas as pd
import pytest

from src.estilo import COR_MW, COR_WELCH
from src.graficos import ORDEM_SITUACOES, grafico_g3, grafico_g4


def _df_exemplo():
    linhas = []
    for pergunta, situacao, n in (
        ("Q1", "base", 30),
        ("Q2", "base", 30),
        ("Q3", "assimetria_extrema", 30),
        ("Q3", "com_outliers", 30),
        ("Q3", "amostra_pequena", 10),
    ):
        efeitos = [0.0] if pergunta == "Q1" else [0.0, 0.5, 0.9]
        for teste, base in (("welch", 0.02), ("mann_whitney", 0.05)):
            for efeito in efeitos:
                taxa = base + efeito * (0.9 if teste == "mann_whitney" else 0.3)
                if pergunta == "Q2" and efeito == 0:
                    taxa += 0.001  # distingue o ponto 0 da Q2 do da Q1
                linhas.append(
                    dict(pergunta=pergunta, situacao=situacao, teste=teste, efeito=efeito,
                         n_por_grupo=n, n_rep=10000, taxa_rejeicao=taxa,
                         ic95_inf=taxa - 0.004, ic95_sup=taxa + 0.004)
                )
    return pd.DataFrame(linhas)


def _tracos_de_dados(fig):
    return [t for t in fig.data if t.name in ("t de Welch", "Mann-Whitney") and t.showlegend is not False]


def test_g3_um_ponto_por_situacao_e_teste_nas_cores_padrao():
    fig = grafico_g3(_df_exemplo())
    tracos = _tracos_de_dados(fig)
    assert {t.name: t.marker.color for t in tracos} == {"t de Welch": COR_WELCH, "Mann-Whitney": COR_MW}
    assert all(len(t.x) == len(ORDEM_SITUACOES) for t in tracos)
    assert all(t.error_x.array is not None for t in tracos)


def test_g3_usa_q1_na_situacao_base_e_efeito_zero_da_q3():
    fig = grafico_g3(_df_exemplo())
    welch = next(t for t in fig.data if t.name == "t de Welch")
    np.testing.assert_allclose(welch.x, [0.02] * 4)  # Q1 (sem o +0,001 da Q2)


def test_g3_linha_de_referencia_segue_o_alpha():
    for alpha in (0.05, 0.01):
        fig = grafico_g3(_df_exemplo(), alpha=alpha)
        assert any(s.type == "line" and s.x0 == pytest.approx(alpha) for s in fig.layout.shapes)
        assert any(s.type == "rect" for s in fig.layout.shapes)  # faixa do acaso


def test_g4_um_painel_por_situacao_com_eixo_y_compartilhado():
    fig = grafico_g4(_df_exemplo())
    linhas = [t for t in fig.data if t.mode and "lines" in t.mode]
    assert len(linhas) == 2 * len(ORDEM_SITUACOES)
    assert {t.line.color for t in linhas} == {COR_WELCH, COR_MW}
    eixos_y = [k for k in fig.layout if k.startswith("yaxis")]
    assert len(eixos_y) == 4
    assert all(tuple(fig.layout[k].range) == (0, 1) for k in eixos_y)


def test_g4_tem_linha_de_80_por_cento_em_cada_painel():
    fig = grafico_g4(_df_exemplo())
    linhas_80 = [s for s in fig.layout.shapes if s.y0 == 0.8 and s.y1 == 0.8]
    assert len(linhas_80) == 4


def test_g4_usa_q2_no_painel_base():
    fig = grafico_g4(_df_exemplo())
    mw_base = next(t for t in fig.data if t.name == "Mann-Whitney" and t.xaxis in (None, "x"))
    assert mw_base.y[0] == pytest.approx(0.051)
