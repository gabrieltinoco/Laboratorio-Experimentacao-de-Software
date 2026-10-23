"""Testes da comparação de resultados de replicação."""

from __future__ import annotations

import pandas as pd
import pytest

from replicacao.comparar import CATEGORIAS, METRICAS, comparar, salvar


def dados(repositorio: str, **sobrescritas) -> dict:
    linha = {
        "repositorio": repositorio,
        **{metrica: 1.0 for metrica in METRICAS},
        **{categoria: "High" for categoria in CATEGORIAS},
    }
    linha.update(sobrescritas)
    return linha


def test_comparar_calcula_diferenca_relativa_e_concordancia():
    referencia = pd.DataFrame([
        dados("o/a", deploy_freq_semana=2.0, categoria_geral="High"),
        dados("o/b", deploy_freq_semana=0.0, categoria_geral="Low"),
        dados("o/so-referencia"),
    ])
    replicacao = pd.DataFrame([
        dados("o/a", deploy_freq_semana=3.0, categoria_geral="High"),
        dados("o/b", deploy_freq_semana=2.0, categoria_geral="High"),
        dados("o/so-replicacao"),
    ])

    metricas, categorias, divergencias_metricas, divergencias_categorias, ausentes = comparar(
        referencia, replicacao
    )
    frequencia = metricas.set_index("metrica").loc["deploy_freq_semana"]
    geral = categorias.set_index("categoria").loc["categoria_geral"]

    assert frequencia["repositorios_comuns"] == 2
    assert frequencia["n_comparaveis"] == 2
    assert frequencia["n_referencia_zero"] == 1
    assert frequencia["diferenca_relativa_media_pct"] == pytest.approx(50)
    assert frequencia["diferenca_relativa_absoluta_media_pct"] == pytest.approx(50)
    assert geral["percentual_igual"] == pytest.approx(50)
    assert set(divergencias_metricas["repositorio"]) == {"o/a", "o/b"}
    assert divergencias_categorias["repositorio"].tolist() == ["o/b"]
    assert set(ausentes["situacao"]) == {
        "ausente na replicação",
        "ausente na referência",
    }


def test_comparar_rejeita_colunas_ausentes_e_repositorios_duplicados():
    referencia = pd.DataFrame([dados("o/a")])
    replicacao = pd.DataFrame([dados("o/a")])
    with pytest.raises(ValueError, match="colunas obrigatórias"):
        comparar(referencia.drop(columns=["cfr_ci"]), replicacao)
    with pytest.raises(ValueError, match="duplicados"):
        comparar(pd.concat([referencia, referencia]), replicacao)


def test_salvar_gera_tabelas_e_relatorio(tmp_path):
    resultados = comparar(
        pd.DataFrame([dados("o/a")]),
        pd.DataFrame([dados("o/a", categoria_geral="Low")]),
    )

    salvar(resultados, tmp_path)

    assert {p.name for p in tmp_path.iterdir()} == {
        "metricas.csv",
        "classificacoes.csv",
        "divergencias_metricas.csv",
        "divergencias_classificacao.csv",
        "divergencias_repositorios.csv",
        "relatorio.md",
    }
    assert "Comparação da replicação" in (tmp_path / "relatorio.md").read_text(encoding="utf-8")
