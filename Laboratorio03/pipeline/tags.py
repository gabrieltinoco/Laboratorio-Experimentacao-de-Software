"""Coleta de tags e da data do commit apontado por cada tag, via GraphQL."""

from __future__ import annotations

from datetime import date, datetime, timezone

from pipeline.http_client import GitHubClient

_ALVO = "... on Commit { oid committedDate author { date } }"

# Tags anotadas apontam para um objeto Tag; seguimos ate dois niveis de tag
# aninhada ate chegar ao commit.
CONSULTA_TAGS = f"""
query($owner: String!, $name: String!, $cursor: String) {{
  repository(owner: $owner, name: $name) {{
    refs(refPrefix: "refs/tags/", first: 100, after: $cursor,
         orderBy: {{field: TAG_COMMIT_DATE, direction: DESC}}) {{
      pageInfo {{ hasNextPage endCursor }}
      nodes {{
        name
        target {{
          {_ALVO}
          ... on Tag {{ target {{ {_ALVO} ... on Tag {{ target {{ {_ALVO} }} }} }} }}
        }}
      }}
    }}
  }}
}}
"""


def _commit(alvo: dict | None) -> dict | None:
    """Desce pelas tags anotadas ate o commit; None se a tag aponta para arvore/blob."""
    while alvo:
        if "oid" in alvo:
            return alvo
        alvo = alvo.get("target")
    return None


def _utc(data: str) -> str:
    """O GraphQL devolve a data com o fuso do autor; o dataset usa UTC, como o REST."""
    instante = datetime.fromisoformat(data.replace("Z", "+00:00")).astimezone(timezone.utc)
    return instante.strftime("%Y-%m-%dT%H:%M:%SZ")


def coletar_tags(cliente: GitHubClient, repositorio: str, inicio: str | date) -> list[dict]:
    """Tags com a data UTC (`commit.author.date`) do commit apontado.

    As tags vem da mais nova para a mais antiga pela data do commit, entao a
    coleta para na primeira pagina inteiramente anterior ao inicio da janela.
    """
    dono, nome = repositorio.split("/", 1)
    inicio = str(inicio)
    registros: list[dict] = []
    cursor = None
    while True:
        refs = cliente.graphql(CONSULTA_TAGS, {"owner": dono, "name": nome, "cursor": cursor})["repository"]["refs"]
        datas_commit = []
        for no in refs["nodes"]:
            commit = _commit(no["target"])
            if commit is None:
                continue
            data_commit = (commit.get("author") or {}).get("date")
            if not data_commit:
                raise ValueError(f"Commit da tag {repositorio}@{no['name']} sem commit.author.date.")
            registros.append({"tag_name": no["name"], "commit_sha": commit["oid"], "commit_date": _utc(data_commit)})
            datas_commit.append(commit["committedDate"][:10])
        if not refs["pageInfo"]["hasNextPage"] or (datas_commit and max(datas_commit) < inicio):
            return registros
        cursor = refs["pageInfo"]["endCursor"]
