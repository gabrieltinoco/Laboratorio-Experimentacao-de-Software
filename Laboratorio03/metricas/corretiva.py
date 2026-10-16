"""Heurística v1 para identificar releases corretivas."""

from __future__ import annotations

import re

_IDENTIFICADOR_PRERELEASE = r"(?:0|[1-9]\d*|[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*)"
_SEMVER = re.compile(
    rf"^v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    rf"(?:-{_IDENTIFICADOR_PRERELEASE}(?:\.{_IDENTIFICADOR_PRERELEASE})*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)
_MENSAGEM_CORRETIVA = re.compile(r"\b(?:fix|hotfix|revert|bugfix)\b", re.IGNORECASE)


def _patch_incrementado(tag_anterior: str | None, tag_atual: str | None) -> bool:
    if not tag_anterior or not tag_atual:
        return False
    anterior = _SEMVER.fullmatch(tag_anterior.strip())
    atual = _SEMVER.fullmatch(tag_atual.strip())
    if anterior is None or atual is None:
        return False
    major_anterior, minor_anterior, patch_anterior = map(int, anterior.groups())
    major_atual, minor_atual, patch_atual = map(int, atual.groups())
    return (
        major_atual == major_anterior
        and minor_atual == minor_anterior
        and patch_atual > patch_anterior
    )


def release_corretiva(
    tag_anterior: str | None, tag_atual: str | None, mensagens: list[str | None]
) -> bool:
    """Marca corretiva por incremento isolado de patch e/ou mensagem de commit."""
    return _patch_incrementado(tag_anterior, tag_atual) or any(
        mensagem is not None and _MENSAGEM_CORRETIVA.search(mensagem)
        for mensagem in mensagens
    )


def classificar_comparacoes(comparacoes: list[dict]) -> dict[str, bool]:
    """Classifica as releases que possuem comparação entre tags coletada."""
    return {
        comparacao["tag_release"]: release_corretiva(
            comparacao.get("tag_anterior"),
            comparacao.get("tag_release"),
            [commit.get("message") for commit in comparacao.get("commits", [])],
        )
        for comparacao in comparacoes
        if comparacao.get("tag_release")
    }
