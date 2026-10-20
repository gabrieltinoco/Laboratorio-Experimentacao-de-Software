"""Testes da coleta de tags e suas datas sem acesso a rede."""

from __future__ import annotations

import pytest

from pipeline.tags import coletar_tags


def commit(sha, autor, commit_em=None):
    return {"oid": sha, "committedDate": commit_em or autor, "author": {"date": autor}}


def pagina(nos, proximo=None):
    return {"repository": {"refs": {
        "pageInfo": {"hasNextPage": proximo is not None, "endCursor": proximo},
        "nodes": nos,
    }}}


class ClienteTags:
    def __init__(self, *paginas):
        self.paginas = list(paginas)
        self.variaveis = []

    def graphql(self, consulta, variaveis=None):
        self.variaveis.append(variaveis)
        return self.paginas.pop(0)


def test_coletar_tags_usa_data_author_em_utc_e_segue_tags_anotadas():
    cliente = ClienteTags(pagina([
        {"name": "v1.1", "target": commit("sha2", "2026-02-03T10:00:00-03:00")},
        {"name": "v1.0", "target": {"target": commit("sha1", "2026-01-05T12:00:00Z")}},
        {"name": "arvore", "target": {}},
    ]))

    tags = coletar_tags(cliente, "o/r", "2025-10-01")

    assert tags == [
        {"tag_name": "v1.1", "commit_sha": "sha2", "commit_date": "2026-02-03T13:00:00Z"},
        {"tag_name": "v1.0", "commit_sha": "sha1", "commit_date": "2026-01-05T12:00:00Z"},
    ]
    assert cliente.variaveis == [{"owner": "o", "name": "r", "cursor": None}]


def test_coletar_tags_para_na_primeira_pagina_anterior_a_janela():
    cliente = ClienteTags(
        pagina([{"name": "v3", "target": commit("s3", "2026-03-01T00:00:00Z")}], proximo="c1"),
        pagina([{"name": "v2", "target": commit("s2", "2025-09-01T00:00:00Z")}], proximo="c2"),
        pagina([{"name": "v1", "target": commit("s1", "2024-01-01T00:00:00Z")}]),
    )

    tags = coletar_tags(cliente, "o/r", "2025-10-01")

    assert [t["tag_name"] for t in tags] == ["v3", "v2"]
    assert [v["cursor"] for v in cliente.variaveis] == [None, "c1"]


def test_coletar_tags_explica_quando_data_do_commit_nao_esta_disponivel():
    cliente = ClienteTags(pagina([{"name": "v1", "target": {"oid": "s", "committedDate": "2026-01-01", "author": {}}}]))

    with pytest.raises(ValueError, match="commit.author.date"):
        coletar_tags(cliente, "o/r", "2025-10-01")
