"""Fixtures numéricas e casos de borda das funções de métrica DORA."""

from __future__ import annotations

from datetime import date

import pytest

from metricas.cfr import change_failure_rate, classificar_conclusion
from metricas.cfr_release import calcular_cfr_releases
from metricas.classificacao import (
    classificar_cfr,
    classificar_frequencia,
    classificar_geral,
    classificar_lead_time,
    classificar_recuperacao,
)
from metricas.corretiva import release_corretiva
from metricas.deploy_freq import (
    deployment_frequency,
    deployment_frequency_com_prereleases,
    deployment_frequency_tags,
)
from metricas.lead_time import lead_time_por_commit, lead_time_por_release
from metricas.recuperacao import calcular_recuperacao
from metricas.rework import calcular_rework


def run(conclusion, inicio, fim=None, workflow=1, started=None):
    return {
        "workflow_id": workflow,
        "conclusion": conclusion,
        "run_started_at": started or inicio,
        "updated_at": fim or inicio,
    }


def test_deployment_frequency_exclui_drafts_prereleases_e_fora_da_janela():
    releases = [
        {"published_at": "2025-10-02T00:00:00Z"},
        {"published_at": "2025-10-03T00:00:00Z", "draft": True},
        {"published_at": "2025-10-04T00:00:00Z", "prerelease": True},
        {"published_at": "2025-09-30T23:00:00Z"},
        {"published_at": None},
    ]
    assert deployment_frequency(releases, date(2025, 10, 1), date(2025, 10, 7)) == 1


def test_deployment_frequency_rejeita_janela_invertida():
    with pytest.raises(ValueError):
        deployment_frequency([], "2025-10-02", "2025-10-01")


def test_deployment_frequency_variantes_incluem_prereleases_ou_tags():
    releases = [
        {"published_at": "2025-10-02T00:00:00Z"},
        {"published_at": "2025-10-03T00:00:00Z", "prerelease": True},
        {"published_at": "2025-10-04T00:00:00Z", "draft": True},
    ]
    tags = [
        {"commit_date": "2025-10-02T00:00:00Z"},
        {"commit_date": "2025-10-07T00:00:00Z"},
        {"commit_date": "2025-09-30T00:00:00Z"},
    ]

    assert deployment_frequency_com_prereleases(releases, "2025-10-01", "2025-10-07") == 2
    assert deployment_frequency_tags(tags, "2025-10-01", "2025-10-07") == 2


@pytest.mark.parametrize(
    ("anterior", "atual", "mensagens", "esperado"),
    [
        ("v2.3.0", "v2.3.1", [], True),
        ("v2.3.0", "v2.4.0", [], False),
        ("v2.3.0", "v2.3.1", ["feat: nova tela"], True),
        ("release-antiga", "release-nova", ["hotfix: crash"], True),
        ("v2.3.0", "v2.3.1", ["revert: regressão"], True),
        ("v2.3.0", "v2.3.1-rc.1", [], True),
        ("v2.3.1", "v2.3.0", [], False),
        ("release-1.0", "release-1.1", ["prefix: fixing parser"], False),
        ("v2.03.0", "v2.03.1", [], False),
        ("v2.3.0-..rc", "v2.3.1-..rc", [], False),
    ],
)
def test_heuristica_corretiva_v1(anterior, atual, mensagens, esperado):
    assert release_corretiva(anterior, atual, mensagens) is esperado


def test_cfr_releases_aplica_janela_de_sete_dias_e_censura():
    releases = [
        {"tag_name": "v2.3.0", "published_at": "2026-09-01T10:00:00Z"},
        {"tag_name": "v2.3.1", "published_at": "2026-09-07T10:00:00Z"},
        {"tag_name": "v2.4.0", "published_at": "2026-09-10T10:00:00Z"},
        {"tag_name": "v2.4.1", "published_at": "2026-09-29T10:00:00Z"},
        {"tag_name": "v2.4.2-rc", "published_at": "2026-09-29T11:00:00Z", "prerelease": True},
    ]
    comparacoes = [
        {"tag_anterior": "v2.3.0", "tag_release": "v2.3.1", "commits": []},
        {"tag_anterior": "v2.4.0", "tag_release": "v2.4.1", "commits": []},
    ]

    resumo = calcular_cfr_releases(releases, comparacoes, "2026-09-01", "2026-09-30")

    assert resumo.releases_avaliadas == 3
    assert resumo.releases_falhas == 1
    assert resumo.releases_censuradas == 1
    assert resumo.cfr == pytest.approx(1 / 3)


def test_cfr_releases_com_falha_nunca_recuperada_conta_se_nao_censurada():
    releases = [{"tag_name": "v1.0", "published_at": "2026-09-01T00:00:00Z"}]
    resumo = calcular_cfr_releases(releases, [], "2026-09-01", "2026-09-30")

    assert resumo.releases_avaliadas == 1
    assert resumo.releases_falhas == 0
    assert resumo.cfr == 0


def test_cfr_releases_sem_denominador_fica_indefinido():
    releases = [{"tag_name": "v1.0", "published_at": "2026-09-30T00:00:00Z"}]
    resumo = calcular_cfr_releases(releases, [], "2026-09-01", "2026-09-30")

    assert resumo.releases_avaliadas == 0
    assert resumo.releases_censuradas == 1
    assert resumo.cfr is None


def test_cfr_releases_ignora_releases_fora_da_janela():
    releases = [
        {"tag_name": "v0.9", "published_at": "2026-08-30T00:00:00Z"},
        {"tag_name": "v1.0", "published_at": "2026-09-01T00:00:00Z"},
        {"tag_name": "v1.1", "published_at": "2026-09-02T00:00:00Z"},
        {"tag_name": "v1.2", "published_at": "2026-10-01T00:00:00Z"},
    ]
    comparacoes = [
        {"tag_anterior": "v1.0", "tag_release": "v1.1", "commits": []},
        {"tag_anterior": "v1.1", "tag_release": "v1.2", "commits": [{"message": "fix: after window"}]},
    ]

    resumo = calcular_cfr_releases(releases, comparacoes, "2026-09-01", "2026-09-30")

    assert resumo.releases_avaliadas == 2
    assert resumo.releases_falhas == 0
    assert resumo.cfr == 0


def test_lead_time_fixture_do_enunciado():
    comparacoes = [
        {
            "published_at": "2025-03-15T00:00:00Z",
            "commits": [
                {"author_date": "2025-03-02T00:00:00Z"},
                {"author_date": "2025-03-10T00:00:00Z"},
                {"author_date": "2025-03-14T00:00:00Z"},
            ],
        }
    ]
    assert lead_time_por_release(comparacoes) == 13
    assert lead_time_por_commit(comparacoes) == 5


def test_lead_time_ignora_release_sem_commits_novas_ou_sem_datas():
    comparacoes = [
        {"published_at": "2025-03-15T00:00:00Z", "commits": []},
        {
            "published_at": "2025-03-15T00:00:00Z",
            "commits": [{"author_date": None}],
        },
    ]
    assert lead_time_por_release(comparacoes) is None
    assert lead_time_por_commit(comparacoes) is None


def test_classificacao_de_conclusions_e_cfr_ignora_runs_neutras():
    assert classificar_conclusion("success") == "sucesso"
    assert classificar_conclusion("timed_out") == "falha"
    for conclusion in ("cancelled", "skipped", "neutral", "action_required", "stale", None):
        assert classificar_conclusion(conclusion) == "ignorar"
    runs = [
        {"conclusion": "success"},
        {"conclusion": "failure"},
        {"conclusion": "startup_failure"},
        {"conclusion": "cancelled"},
        {"conclusion": None},
    ]
    assert change_failure_rate(runs) == pytest.approx(2 / 3)
    assert change_failure_rate([{"conclusion": "cancelled"}]) is None


def test_recuperacao_fixture_do_enunciado_e_ignora_cancelada_sem_timestamps():
    runs = [
        run("success", "2025-10-01T09:00:00Z"),
        run("failure", "2025-10-01T10:00:00Z", started="2025-10-01T10:00:00Z"),
        run("cancelled", "x", started=None),
        run("failure", "2025-10-01T10:30:00Z", started="2025-10-01T10:30:00Z"),
        run(
            "success",
            "2025-10-01T11:20:00Z",
            started="2025-10-01T11:15:00Z",
        ),
    ]
    resumo = calcular_recuperacao(runs)
    assert resumo.mediana_horas == pytest.approx(4 / 3)
    assert resumo.censurados == 0
    assert resumo.proporcao_censurados == 0


def test_recuperacao_registra_falha_nao_recuperada_como_censurada():
    runs = [
        run("success", "2025-10-01T09:00:00Z", workflow=1),
        run("failure", "2025-10-01T10:00:00Z", workflow=1),
        run("success", "2025-10-01T09:00:00Z", workflow=2),
        run("failure", "2025-10-01T10:00:00Z", workflow=2),
    ]
    resumo = calcular_recuperacao(runs)
    assert resumo.mediana_horas is None
    assert len(resumo.episodios) == 2
    assert resumo.censurados == 2
    assert resumo.proporcao_censurados == 1
    assert all(episodio.fim is None and episodio.censurado for episodio in resumo.episodios)


def test_recuperacao_que_termina_depois_da_janela_permanece_censurada():
    runs = [
        run("success", "2025-10-31T09:00:00Z"),
        run("failure", "2025-10-31T10:00:00Z"),
        run(
            "success",
            "2025-11-01T00:05:00Z",
            started="2025-10-31T23:55:00Z",
        ),
    ]

    resumo = calcular_recuperacao(runs, fim_janela="2025-10-31")

    assert resumo.mediana_horas is None
    assert resumo.censurados == 1
    assert resumo.proporcao_censurados == 1


def test_recuperacao_nao_cria_episodio_antes_de_observar_sucesso():
    resumo = calcular_recuperacao([run("failure", "2025-10-01T10:00:00Z")])
    assert resumo.episodios == ()
    assert resumo.proporcao_censurados is None


def test_recuperacao_erro_claro_quando_falta_timestamp_de_run_avaliavel():
    with pytest.raises(ValueError, match="run_started_at"):
        calcular_recuperacao([{"workflow_id": 1, "conclusion": "success"}])


def test_classificacoes_dora_e_classificacao_geral():
    assert [classificar_frequencia(valor) for valor in (7, 1, 0.25, 0)] == [
        "Elite", "High", "Medium", "Low"
    ]
    assert [classificar_lead_time(valor) for valor in (0.5, 1, 7, 30)] == [
        "Elite", "High", "Medium", "Low"
    ]
    assert [classificar_cfr(valor) for valor in (0.15, 0.16, 0.31, 0.46)] == [
        "Elite", "High", "Medium", "Low"
    ]
    assert [classificar_recuperacao(valor) for valor in (0.5, 1, 24, 168)] == [
        "Elite", "High", "Medium", "Low"
    ]
    assert classificar_geral(["Elite", "High", "High", "Low"]) == "High"


@pytest.mark.parametrize(
    ("classificador", "valor"),
    [
        (classificar_frequencia, -1),
        (classificar_lead_time, float("inf")),
        (classificar_cfr, 1.1),
        (classificar_recuperacao, -1),
    ],
)
def test_classificacao_rejeita_valores_invalidos(classificador, valor):
    with pytest.raises(ValueError):
        classificador(valor)


def test_classificacao_geral_exige_quatro_categorias_validas():
    with pytest.raises(ValueError):
        classificar_geral(["Elite", "Low"])
    with pytest.raises(ValueError):
        classificar_geral(["Elite", "High", "Other", "Low"])


def comparacao(anterior, atual, mensagens):
    return {"tag_anterior": anterior, "tag_release": atual,
            "commits": [{"message": mensagem} for mensagem in mensagens]}


def test_rework_conta_corretivas_sobre_todas_as_releases_da_janela():
    comparacoes = [
        comparacao("v2.3.0", "v2.3.1", ["fix: crash ao abrir arquivo"]),
        comparacao("v2.3.1", "v2.4.0", ["feat: exportar PDF"]),
        comparacao("v2.4.0", "v2.5.0", ["revert: exportar PDF"]),
    ]
    # Quatro releases na janela: a primeira não tem compare e só entra no denominador.
    resumo = calcular_rework(comparacoes, releases_na_janela=4)

    assert resumo.releases_corretivas == 2
    assert resumo.rework_rate == pytest.approx(0.5)


def test_rework_sem_releases_fica_indefinido():
    assert calcular_rework([], 0).rework_rate is None


def test_rework_rejeita_contagens_inconsistentes():
    with pytest.raises(ValueError):
        calcular_rework([comparacao("v1.0.0", "v1.0.1", [])], 0)
    with pytest.raises(ValueError):
        calcular_rework([], -1)
