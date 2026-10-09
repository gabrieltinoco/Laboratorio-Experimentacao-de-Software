"""Fixtures numéricas e casos de borda das funções de métrica DORA."""

from __future__ import annotations

from datetime import date

import pytest

from metricas.cfr import change_failure_rate, classificar_conclusion
from metricas.classificacao import (
    classificar_cfr,
    classificar_frequencia,
    classificar_geral,
    classificar_lead_time,
    classificar_recuperacao,
)
from metricas.deploy_freq import deployment_frequency
from metricas.lead_time import lead_time_por_commit, lead_time_por_release
from metricas.recuperacao import calcular_recuperacao


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
