"""Análises da S03 rodando sobre um CSV pequeno construído à mão."""

from __future__ import annotations

import pandas as pd
import pytest

from analise import comum, rq01_04, rq05_rq08


@pytest.fixture
def dataset():
    return pd.DataFrame({
        "repositorio": ["o/a", "o/b", "o/c", "o/d"],
        "deploy_freq_semana": [8.0, 2.0, 0.5, 0.1],
        "lead_time_release_dias": [0.5, 10.0, 40.0, None],
        "lead_time_commit_dias": [0.25, 2.0, 40.0, None],
        "cfr_ci": [0.1, 0.2, 0.4, 0.6],
        "cfr_releases": [0.0, 0.25, 0.5, None],
        "rework_rate": [0.1, 0.25, 0.4, 0.0],
        "recuperacao_horas": [0.5, 5.0, 30.0, 200.0],
        "episodios_falha": [2, 4, 0, 5],
        "episodios_censurados": [0, 1, 0, 5],
        "proporcao_censurados": [0.0, 0.25, None, 1.0],
    })


def test_resumo_reporta_mediana_e_iqr_sem_vazios():
    r = comum.resumo(pd.Series([1, 2, 3, 4, None]))

    assert (r["n"], r["mediana"], r["q1"], r["q3"]) == (4, 2.5, 1.75, 3.25)
    assert r["iqr"] == pytest.approx(1.5)
    assert comum.resumo(pd.Series([], dtype=float))["mediana"] is None


def test_classificacao_c1_e_geral_vazia_sem_alguma_metrica(dataset):
    c1 = comum.classificacao_c1(dataset).set_index("repositorio")

    assert list(c1.loc["o/a"]) == ["Elite", "Elite", "Elite", "Elite", "Elite"]
    assert list(c1.loc["o/c"]) == ["Medium", "Low", "Medium", "Medium", "Medium"]
    assert c1.loc["o/d", "categoria_lead_time"] is None
    assert c1.loc["o/d", "categoria_geral"] is None


def test_distribuicao_categorias_soma_100_por_metrica(dataset):
    dist = comum.distribuicao_categorias(comum.classificacao_c1(dataset))

    assert dist.groupby("metrica")["pct"].sum().tolist() == pytest.approx([100] * 5)
    lead = dist[dist["metrica"] == "lead_time"].set_index("categoria")["n"]
    assert lead.sum() == 3


def test_censura_e_divergencia_do_lead_time(dataset):
    censura = rq01_04.censura(dataset).iloc[0]
    assert (censura["episodios"], censura["episodios_censurados"]) == (11, 6)
    assert censura["repositorios_sem_episodio"] == 1

    divergencia = rq01_04.divergencia_lead_time(dataset).iloc[0]
    assert divergencia["repositorios"] == 3
    assert divergencia["pct_a_maior_que_b"] == pytest.approx(200 / 3)
    assert divergencia["razao_a_b_mediana"] == pytest.approx(2)


def test_spearman_e_rework(dataset):
    correlacoes = rq05_rq08.spearman_rq05(dataset).set_index("y")
    assert correlacoes.loc["cfr_ci", "rho"] == pytest.approx(-1)
    assert correlacoes.loc["cfr_releases", "n"] == 3

    rework = rq05_rq08.rework_vs_cfr(dataset).iloc[0]
    assert rework["n"] == 3
    assert rework["pct_iguais"] == pytest.approx(100 / 3)


def test_scripts_gravam_tabelas_e_figuras(dataset, tmp_path):
    csv = tmp_path / "repositorios.csv"
    dataset.to_csv(csv, index=False)
    argv = ["--dados", str(csv), "--saidas", str(tmp_path / "saidas")]

    comum.main(argv)
    rq01_04.main(argv)
    rq05_rq08.main(argv)

    gerados = {p.name for p in (tmp_path / "saidas").iterdir()}
    for nome in ("classificacao_c1.csv", "rq01_04_resumo.md", "rq04_censura.csv",
                 "rq01_04_distribuicoes.png", "rq01_04_categorias_c1.png",
                 "rq05_spearman.csv", "rq05_dispersao.png", "rq08_rework_vs_cfr.png"):
        assert nome in gerados
