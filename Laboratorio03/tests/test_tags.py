"""Testes da coleta de tags e suas datas sem acesso a rede."""

from __future__ import annotations

import pytest

from pipeline.http_client import Resposta
from pipeline.tags import coletar_tags


class ClienteTags:
    def __init__(self):
        self.referencias = []

    def get_todos(self, caminho, params=None, chave=None):
        assert caminho == "/repos/o/r/tags"
        return [{"name": "v1.0", "commit": {"sha": "sha1"}}]

    def get(self, caminho):
        self.referencias.append(caminho)
        return Resposta(
            200,
            caminho,
            {"sha": "sha1", "commit": {"author": {"date": "2026-02-03T10:00:00Z"}}},
        )


def test_coletar_tags_usa_data_author_do_commit_apontado():
    cliente = ClienteTags()

    tags = coletar_tags(cliente, "o/r")

    assert tags == [{
        "tag_name": "v1.0",
        "commit_sha": "sha1",
        "commit_date": "2026-02-03T10:00:00Z",
    }]
    assert cliente.referencias == ["/repos/o/r/commits/v1.0"]


def test_coletar_tags_explica_quando_data_do_commit_nao_esta_disponivel():
    class ClienteSemData(ClienteTags):
        def get(self, caminho):
            return Resposta(200, caminho, {"sha": "sha1", "commit": {"author": {}}})

    with pytest.raises(ValueError, match="commit.author.date"):
        coletar_tags(ClienteSemData(), "o/r")
