"""Testes do histograma G1 de dados reais e simulados."""

import pandas as pd

from src.graficos import grafico_g1


def _df_grupo(multiplicador: float) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "grupo": ["sem_bot", "sem_bot", "com_bot", "com_bot"],
            "horas_ate_merge": [
                1.0 * multiplicador,
                10.0 * multiplicador,
                2.0 * multiplicador,
                20.0 * multiplicador,
            ],
        }
    )


def test_g1_compara_frequencias_com_mesmos_bins_e_rotulos():
    figura = grafico_g1(_df_grupo(1.0), _df_grupo(1.5))
    histogramas = [traco for traco in figura.data if traco.type == "histogram"]

    assert len(histogramas) == 2
    assert all(traco.histnorm is None for traco in histogramas)
    assert all(traco.xbins == histogramas[0].xbins for traco in histogramas)
    assert figura.layout.yaxis.title.text == "Frequência (PRs por intervalo)"
    assert "Tempo até merge (horas" in figura.layout.xaxis.title.text
