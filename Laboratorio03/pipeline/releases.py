"""Coleta de releases e commits entre releases pela API REST do GitHub."""

from __future__ import annotations

import logging
from datetime import date, datetime
from urllib.parse import quote

from pipeline.http_client import ErroGitHub, GitHubClient

log = logging.getLogger(__name__)


def _data_api(valor: str | None) -> date | None:
    if not valor:
        return None
    return datetime.fromisoformat(valor.replace("Z", "+00:00")).date()


def _release_principal(release: dict) -> bool:
    return not release.get("draft", False) and not release.get("prerelease", False)


def coletar_releases(
    cliente: GitHubClient, repositorio: str, inicio: str | date, fim: str | date
) -> list[dict]:
    """Retorna releases na janela e a release principal imediatamente anterior."""
    inicio = date.fromisoformat(inicio) if isinstance(inicio, str) else inicio
    fim = date.fromisoformat(fim) if isinstance(fim, str) else fim
    releases = cliente.get_todos(f"/repos/{repositorio}/releases")
    normalizadas = [
        {
            "id": release.get("id"),
            "tag_name": release.get("tag_name"),
            "draft": bool(release.get("draft", False)),
            "prerelease": bool(release.get("prerelease", False)),
            "published_at": release.get("published_at"),
            "created_at": release.get("created_at"),
            "html_url": release.get("html_url"),
            "name": release.get("name"),
            "body": release.get("body"),
        }
        for release in releases
    ]

    anteriores = [
        release for release in normalizadas
        if _release_principal(release)
        and (data := _data_api(release["published_at"])) is not None
        and data < inicio
    ]
    na_janela = [
        release for release in normalizadas
        if (data := _data_api(release["published_at"])) is not None
        and inicio <= data <= fim
    ]
    # Drafts podem não ter published_at; created_at permite preservá-los para auditoria.
    na_janela.extend(
        release for release in normalizadas
        if release["draft"]
        and (data := _data_api(release["created_at"])) is not None
        and inicio <= data <= fim
    )
    selecionadas = na_janela
    if anteriores:
        selecionadas.append(max(anteriores, key=lambda r: r["published_at"]))

    return sorted(
        {release["id"]: release for release in selecionadas}.values(),
        key=lambda release: (
            release["published_at"] or release["created_at"] or "",
            str(release["tag_name"] or ""),
        ),
    )


def coletar_commits_entre_releases(
    cliente: GitHubClient,
    repositorio: str,
    releases: list[dict],
    inicio: str | date,
    fim: str | date,
) -> tuple[list[dict], list[dict]]:
    """Compara releases principais consecutivas; devolve comparações e 404s."""
    inicio = date.fromisoformat(inicio) if isinstance(inicio, str) else inicio
    fim = date.fromisoformat(fim) if isinstance(fim, str) else fim
    ordenadas = sorted(
        (
            release for release in releases
            if _release_principal(release) and release.get("published_at") and release.get("tag_name")
        ),
        key=lambda release: release["published_at"],
    )
    comparacoes: list[dict] = []
    ignoradas_404: list[dict] = []

    for anterior, atual in zip(ordenadas, ordenadas[1:]):
        data_atual = _data_api(atual["published_at"])
        if data_atual is None or not inicio <= data_atual <= fim:
            continue

        base = quote(str(anterior["tag_name"]), safe="")
        head = quote(str(atual["tag_name"]), safe="")
        caminho = f"/repos/{repositorio}/compare/{base}...{head}"
        try:
            commits = cliente.get_todos(caminho, {"per_page": cliente.per_page}, chave="commits")
        except ErroGitHub as erro:
            if erro.status != 404:
                raise
            registro = {
                "tag_anterior": anterior["tag_name"],
                "tag_release": atual["tag_name"],
                "status": erro.status,
            }
            ignoradas_404.append(registro)
            log.warning("Compare indisponivel (HTTP 404) em %s: %s", repositorio, caminho)
            continue

        comparacoes.append(
            {
                "tag_anterior": anterior["tag_name"],
                "tag_release": atual["tag_name"],
                "published_at": atual["published_at"],
                "commits": [
                    {
                        "sha": commit.get("sha"),
                        "author_date": (commit.get("commit", {}).get("author") or {}).get("date"),
                        "message": commit.get("commit", {}).get("message"),
                        "html_url": commit.get("html_url"),
                    }
                    for commit in commits
                ],
            }
        )
    return comparacoes, ignoradas_404
