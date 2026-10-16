"""Coleta de tags e da data do commit apontado por cada tag."""

from __future__ import annotations

from urllib.parse import quote

from pipeline.http_client import GitHubClient


def coletar_tags(cliente: GitHubClient, repositorio: str) -> list[dict]:
    """Devolve todas as tags com a data UTC do commit que cada uma aponta."""
    tags = cliente.get_todos(f"/repos/{repositorio}/tags")
    registros = []
    for tag in tags:
        nome = tag.get("name")
        if not nome:
            raise ValueError(f"Resposta de tags de {repositorio} sem nome de tag.")
        referencia = quote(str(nome), safe="")
        commit = cliente.get(f"/repos/{repositorio}/commits/{referencia}").dados
        data_commit = (commit.get("commit", {}).get("author") or {}).get("date")
        if not data_commit:
            raise ValueError(f"Commit da tag {repositorio}@{nome} sem commit.author.date.")
        commit_sha = commit.get("sha") or (tag.get("commit") or {}).get("sha")
        if not commit_sha:
            raise ValueError(f"Commit da tag {repositorio}@{nome} sem SHA.")
        registros.append(
            {
                "tag_name": nome,
                "commit_sha": commit_sha,
                "commit_date": data_commit,
            }
        )
    return registros
