"""Regras de layout que evitam textos sobrepostos nos graficos do dashboard.

O Streamlit coloca os graficos numa coluna estreita (~700 px). A legenda no topo
caia em cima dos titulos dos subgraficos, e anotacoes empilhadas no topo do G1
e no rodape do G2 colidiam com titulos e eixos.
"""

import numpy as np
import pandas as pd
import plotly.io as pio

from src.estilo import TEMPLATE
from src.graficos import grafico_g1, grafico_g2


def _dados(multiplicador):
    return pd.DataFrame(
        {
            "grupo": ["sem_bot"] * 3 + ["com_bot"] * 3,
            "horas_ate_merge": np.array([1.0, 10.0, 100.0, 2.0, 20.0, 200.0]) * multiplicador,
        }
    )


def test_legenda_padrao_fica_no_rodape_fora_da_area_dos_titulos():
    legenda = pio.templates[TEMPLATE].layout.legend
    assert legenda.yref == "container"
    assert legenda.yanchor == "bottom" and legenda.y <= 0.05


def test_g1_sem_anotacoes_de_mediana_empilhadas_no_topo():
    fig = grafico_g1(_dados(1.0), _dados(1.5))
    textos = [a.text for a in fig.layout.annotations]
    assert len(textos) == 2  # so os titulos dos dois paineis
    assert all("mediana" in t.lower() for t in textos)


def test_g1_legenda_sem_entradas_repetidas_e_com_simulados():
    fig = grafico_g1(_dados(1.0), _dados(1.5))
    nomes = [t.name for t in fig.data if t.showlegend is not False]
    assert len(nomes) == len(set(nomes))
    assert any("Simulados" in n for n in nomes) and any("Reais" in n for n in nomes)


def test_g2_p_valores_nos_titulos_e_nada_abaixo_do_eixo():
    fig = grafico_g2(np.arange(1.0, 31.0), np.arange(2.0, 32.0))
    titulos = [a.text for a in fig.layout.annotations if a.yref == "paper" and a.y >= 1]
    assert len(titulos) == 2 and all("p = " in t for t in titulos)
    assert not [a for a in fig.layout.annotations if a.yref == "paper" and a.y < 0]
