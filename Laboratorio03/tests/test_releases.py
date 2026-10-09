"""Testes dos coletores de releases e commits entre releases sem acesso a rede."""

from __future__ import annotations

from datetime import date

import pytest

from pipeline.http_client import ErroGitHub
from pipeline.releases import coletar_commits_entre_releases, coletar_releases


def release(identificador, tag, publicada, *, draft=False, prerelease=False, criada=None):
    return {
        "id": identificador,
        "tag_name": tag,
        "draft": draft,
        "prerelease": prerelease,
        "published_at": publicada,
        "created_at": criada or publicada,
        "html_url": f"https://github.com/o/r/releases/tag/{tag}",
        "name": tag,
        "body": "notas",
    }


class ClienteReleases:
    per_page = 100

    def __init__(self, releases=None, comparacoes=None):
        self.releases = releases or []
        self.comparacoes = comparacoes or {}
        self.chamadas = []

    def get_todos(self, caminho, params=None, chave=None):
        self.chamadas.append((caminho, params, chave))
        if caminho.endswith("/releases"):
            return self.releases
        resultado = self.comparacoes[caminho]
        if isinstance(resultado, Exception):
            raise resultado
        return resultado


def test_coletar_releases_guarda_janela_e_ultima_release_principal_anterior():
    cliente = ClienteReleases([
        release(1, "v1.0", "2025-09-20T00:00:00Z"),
        release(2, "v1.1", "2025-09-25T00:00:00Z", prerelease=True),
        release(3, "v2.0", "2025-10-01T00:00:00Z"),
        release(4, "v2.1", "2025-12-10T00:00:00Z", prerelease=True),
        release(5, "draft", None, draft=True, criada="2025-11-01T00:00:00Z"),
        release(6, "v3.0", "2026-02-01T00:00:00Z"),
    ])

    resultado = coletar_releases(cliente, "o/r", date(2025, 10, 1), date(2025, 12, 31))

    assert [item["tag_name"] for item in resultado] == ["v1.0", "v2.0", "draft", "v2.1"]
    assert resultado[0]["prerelease"] is False
    assert cliente.chamadas == [("/repos/o/r/releases", None, None)]


def test_compare_pagina_e_usa_data_do_autor():
    releases = [
        release(1, "v1.0", "2025-09-01T00:00:00Z"),
        release(2, "v1.1", "2025-10-15T00:00:00Z"),
    ]
    caminho = "/repos/o/r/compare/v1.0...v1.1"
    cliente = ClienteReleases(
        comparacoes={
            caminho: [
                {
                    "sha": "abc",
                    "commit": {
                        "author": {"date": "2025-10-02T00:00:00Z"},
                        "message": "feature",
                    },
                    "html_url": "https://github.com/o/r/commit/abc",
                }
            ]
        }
    )

    comparacoes, erros = coletar_commits_entre_releases(
        cliente, "o/r", releases, "2025-10-01", "2025-10-31"
    )

    assert erros == []
    assert comparacoes == [
        {
            "tag_anterior": "v1.0",
            "tag_release": "v1.1",
            "published_at": "2025-10-15T00:00:00Z",
            "commits": [
                {
                    "sha": "abc",
                    "author_date": "2025-10-02T00:00:00Z",
                    "message": "feature",
                    "html_url": "https://github.com/o/r/commit/abc",
                }
            ],
        }
    ]
    assert cliente.chamadas == [(caminho, {"per_page": 100}, "commits")]


def test_compare_404_e_contado_sem_interromper_as_comparacoes():
    releases = [
        release(1, "v1.0", "2025-09-01T00:00:00Z"),
        release(2, "v1.1", "2025-10-15T00:00:00Z"),
        release(3, "v1.2", "2025-10-25T00:00:00Z"),
    ]
    cliente = ClienteReleases(
        comparacoes={
            "/repos/o/r/compare/v1.0...v1.1": ErroGitHub(404, "url"),
            "/repos/o/r/compare/v1.1...v1.2": [],
        }
    )

    comparacoes, erros = coletar_commits_entre_releases(
        cliente, "o/r", releases, "2025-10-01", "2025-10-31"
    )

    assert len(comparacoes) == 1
    assert erros == [{"tag_anterior": "v1.0", "tag_release": "v1.1", "status": 404}]


def test_compare_propaga_erros_diferentes_de_404():
    releases = [
        release(1, "v1.0", "2025-09-01T00:00:00Z"),
        release(2, "v1.1", "2025-10-15T00:00:00Z"),
    ]
    cliente = ClienteReleases(
        comparacoes={"/repos/o/r/compare/v1.0...v1.1": ErroGitHub(403, "url")}
    )
    with pytest.raises(ErroGitHub):
        coletar_commits_entre_releases(cliente, "o/r", releases, "2025-10-01", "2025-10-31")


def test_compare_nao_compara_prereleases_ou_release_fora_da_janela():
    releases = [
        release(1, "v1.0", "2025-09-01T00:00:00Z"),
        release(2, "v1.1-rc", "2025-10-15T00:00:00Z", prerelease=True),
        release(3, "v1.1", "2025-11-15T00:00:00Z"),
        release(4, "v1.2", "2025-12-15T00:00:00Z"),
    ]
    cliente = ClienteReleases(
        comparacoes={
            "/repos/o/r/compare/v1.0...v1.1": [],
            "/repos/o/r/compare/v1.1...v1.2": [],
        }
    )

    comparacoes, _ = coletar_commits_entre_releases(
        cliente, "o/r", releases, "2025-10-01", "2025-11-30"
    )

    assert [item["tag_release"] for item in comparacoes] == ["v1.1"]
