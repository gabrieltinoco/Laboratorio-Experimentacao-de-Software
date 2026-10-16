"""Testes de avaliação da heurística contra o consenso."""

from __future__ import annotations

import pandas as pd
import pytest

from validacao.avaliar_heuristica import avaliar, registrar


def test_avaliar_calcula_precisao_recall_f1_nos_rotulos_consensuais():
    consenso = pd.DataFrame([
        {"repositorio": "o/r", "tag_name": "v2.3.1", "corretiva": "sim"},
        {"repositorio": "o/r", "tag_name": "release-2", "corretiva": "não"},
        {"repositorio": "o/r", "tag_name": "v2.4.0", "corretiva": "sim"},
        {"repositorio": "o/r", "tag_name": "v2.4.1", "corretiva": "não"},
    ])
    releases = [
        {"repositorio": "o/r", "tag_name": "v2.3.0", "published_at": "2026-01-01T00:00:00Z"},
        {"repositorio": "o/r", "tag_name": "v2.3.1", "published_at": "2026-01-02T00:00:00Z"},
        {"repositorio": "o/r", "tag_name": "release-2", "published_at": "2026-01-03T00:00:00Z"},
        {"repositorio": "o/r", "tag_name": "v2.4.0", "published_at": "2026-01-04T00:00:00Z"},
        {"repositorio": "o/r", "tag_name": "v2.4.1", "published_at": "2026-01-05T00:00:00Z"},
    ]
    comparacoes = [
        {"repositorio": "o/r", "tag_release": "release-2", "commits": [{"message": "feat"}]},
        {"repositorio": "o/r", "tag_release": "v2.4.0", "commits": [{"message": "fix: regression"}]},
    ]

    resultado = avaliar(consenso, releases, comparacoes)

    assert resultado["n"] == 4
    assert resultado["precisao"] == pytest.approx(2 / 3)
    assert resultado["recall"] == pytest.approx(1)
    assert resultado["f1"] == pytest.approx(0.8)


def test_avaliar_recusa_consenso_incompleto():
    consenso = pd.DataFrame([{"repositorio": "o/r", "tag_name": "v1.0", "corretiva": ""}])
    with pytest.raises(ValueError, match="rótulos"):
        avaliar(consenso, [], [])


def test_historico_nao_permite_sobrescrever_versao(tmp_path):
    caminho = tmp_path / "avaliacao.csv"
    resultado = {"n": 1, "precisao": 0.5, "recall": 1.0, "f1": 2 / 3}

    registrar(caminho, "v1", resultado)
    with pytest.raises(ValueError, match="já foi registrada"):
        registrar(caminho, "v1", resultado)

    assert pd.read_csv(caminho)["versao"].tolist() == ["v1"]
