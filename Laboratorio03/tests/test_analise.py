"""Análises da S03 rodando sobre um CSV pequeno construído à mão."""

from __future__ import annotations

import pandas as pd
import pytest

from analise import comum, rq01_04, rq05_rq08, rq06_rq07


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
    assert pd.isna(c1.loc["o/d", "categoria_lead_time"])
    assert pd.isna(c1.loc["o/d", "categoria_geral"])


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


def test_rq06_calcula_holm_efeitos_e_retorna_fatores(dataset):
    dados = dataset.assign(
        linguagem=["Python", "Python", "Go", "Go"],
        estrelas=[100, 200, 300, 400],
        idade_anos=[1, 2, 3, 4],
    )

    testes, efeitos = rq06_rq07.analisar_rq06(dados)

    assert set(testes["fator"]) == set(rq06_rq07.FATORES)
    validos = testes["p_valor"].notna()
    assert testes.loc[validos, "p_holm"].notna().all()
    assert (testes["epsilon_quadrado"].dropna() >= 0).all()
    assert not efeitos.empty
    assert set(efeitos["magnitude_romano"]) <= {"desprezível", "pequeno", "médio", "grande"}


def test_rq06_aceita_tipo_de_projeto_consensual(dataset):
    dados = dataset.assign(
        linguagem=["Python", "Python", "Go", "Go"],
        estrelas=[100, 200, 300, 400],
        idade_anos=[1, 2, 3, 4],
    )
    tipos = pd.Series(
        ["biblioteca/framework", "biblioteca/framework", "ferramenta CLI", "ferramenta CLI"],
        index=dados.index,
    )

    testes, _ = rq06_rq07.analisar_rq06(dados, tipos)

    tipo_projeto = testes[testes["fator"] == "tipo_projeto"]
    assert len(tipo_projeto) == len(rq06_rq07.METRICAS)
    assert (tipo_projeto["n"] >= 2).all()


def test_tipo_projeto_usa_consenso_ou_apenas_acordos_unanimes(tmp_path):
    pasta = tmp_path / "validacao"
    pasta.mkdir()
    avaliador_1 = pd.DataFrame({
        "repositorio": ["o/a", "o/b", "o/c"],
        "tipo_projeto": ["biblioteca/framework", "aplicação/serviço", "outro"],
    })
    avaliador_2 = pd.DataFrame({
        "repositorio": ["o/a", "o/b", "o/c"],
        "tipo_projeto": ["biblioteca/framework", "ferramenta CLI", "outro"],
    })
    for nome, tabela in [
        ("rotulos_avaliador_1.xlsx", avaliador_1),
        ("rotulos_avaliador_2.xlsx", avaliador_2),
    ]:
        with pd.ExcelWriter(pasta / nome) as writer:
            tabela.to_excel(writer, sheet_name="repositorios", index=False)

    tipo = rq06_rq07._tipo_projeto_consensual(pasta, pd.Series(["o/a", "o/b", "o/c"]))

    assert tipo.iloc[0] == "biblioteca/framework"
    assert pd.isna(tipo.iloc[1])
    assert tipo.iloc[2] == "outro"

    consenso = pd.DataFrame({
        "repositorio": ["o/a", "o/b", "o/c"],
        "tipo_projeto": ["biblioteca/framework", "ferramenta CLI", "outro"],
    })
    consenso.to_csv(pasta / "consenso_repositorios.csv", index=False)
    tipo_final = rq06_rq07._tipo_projeto_consensual(pasta, pd.Series(["o/a", "o/b", "o/c"]))

    assert tipo_final.tolist() == ["biblioteca/framework", "ferramenta CLI", "outro"]


def test_rq07_classifica_c1_c2_c3_e_mede_mudancas(dataset):
    dados = dataset.assign(
        deploy_freq_com_prereleases_semana=[8.0, 8.0, 0.1, 0.1],
        deploy_freq_tags_semana=[0.1, 0.1, 8.0, 8.0],
    )

    classificacoes = rq06_rq07.classificar_combinacoes(dados)
    sensibilidade = rq06_rq07.analisar_rq07(classificacoes)

    assert len(classificacoes) == len(dados)
    assert {"C1_categoria_geral", "C2_categoria_geral", "C3_categoria_geral"} <= set(
        classificacoes.columns
    )
    assert len(sensibilidade) == 15
    assert sensibilidade["kappa_ponderado_linear"].notna().all()
    geral = sensibilidade[sensibilidade["categoria"] == "geral"]
    assert (geral["pct_mudaram"] > 0).any()
    assert rq06_rq07.COMBINACOES == {
        "C1": ("deploy_freq_semana", "lead_time_release_dias", "cfr_ci"),
        "C2": (
            "deploy_freq_com_prereleases_semana",
            "lead_time_commit_dias",
            "cfr_releases",
        ),
        "C3": ("deploy_freq_tags_semana", "lead_time_commit_dias", "cfr_ci"),
    }


def test_rq06_sem_variacao_de_fator_retorna_sem_testes_validos(dataset):
    dados = dataset.assign(
        linguagem="Python",
        estrelas=[100, 200, 300, 400],
        idade_anos=[1, 2, 3, 4],
    )

    testes, efeitos = rq06_rq07.analisar_rq06(dados)

    assert not testes["p_valor"].notna().any()
    assert efeitos.empty
