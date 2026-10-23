"""Heurísticas para identificar releases corretivas.

v1: incremento isolado de patch ou qualquer commit com fix/hotfix/revert/bugfix.
v2: notas da release dominadas por correções, ou incremento de patch sem
funcionalidade nas notas e com commits de correção em número igual ou maior
que os de funcionalidade. Desenhada na metade de desenvolvimento da
amostra-ouro (ver validacao/avaliacao_heuristica.csv e a metodologia).
"""

from __future__ import annotations

import re
from typing import Callable

_IDENTIFICADOR_PRERELEASE = r"(?:0|[1-9]\d*|[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*)"
_SEMVER = re.compile(
    rf"^v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    rf"(?:-{_IDENTIFICADOR_PRERELEASE}(?:\.{_IDENTIFICADOR_PRERELEASE})*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)
_MENSAGEM_CORRETIVA = re.compile(r"\b(?:fix|hotfix|revert|bugfix)\b", re.IGNORECASE)

# v2
_CORRECAO = re.compile(r"\b(?:fix|fixes|fixed|hotfix|revert|bugfix)\b", re.IGNORECASE)
_FUNCIONALIDADE = re.compile(
    r"^(?:feat|feature)(?:\(.+?\))?!?:"
    r"|\b(?:add|adds|added|implement|implements|introduce|introduces|support for|new)\b",
    re.IGNORECASE,
)
_COMMIT_DE_RELEASE = re.compile(
    r"^(?:merge|chore\(release\)|release|bump version|v?\d+\.\d+)", re.IGNORECASE
)
_SECAO_CORRECAO = re.compile(
    r"^#+\s*[^\n]*\b(?:bug ?fix(?:es)?|fixe[sd]|fix|patch changes|hotfix)\b",
    re.IGNORECASE | re.MULTILINE,
)
_SECAO_FUNCIONALIDADE = re.compile(
    r"^#+\s*[^\n]*\b(?:features?|added|new|enhancements?|improvements?|highlights)\b",
    re.IGNORECASE | re.MULTILINE,
)
_ITEM = re.compile(r"^\s*[-*]\s+(.*)$", re.MULTILINE)
_ITEM_IGNORADO = re.compile(r"new contributor|full changelog|made their first", re.IGNORECASE)

VERSAO_ATUAL = "v2"


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
    """v1: marca corretiva por incremento isolado de patch e/ou mensagem de commit."""
    return _patch_incrementado(tag_anterior, tag_atual) or any(
        mensagem is not None and _MENSAGEM_CORRETIVA.search(mensagem)
        for mensagem in mensagens
    )


def release_corretiva_v2(
    tag_anterior: str | None,
    tag_atual: str | None,
    mensagens: list[str | None],
    notas: str | None = None,
) -> bool:
    """v2: julga pelas notas da release e usa patch + commits quando as notas não decidem."""
    notas = notas or ""
    itens = [item for item in _ITEM.findall(notas) if not _ITEM_IGNORADO.search(item)]
    itens_correcao = sum(bool(_CORRECAO.search(item)) for item in itens)
    itens_funcionalidade = sum(bool(_FUNCIONALIDADE.search(item)) for item in itens)
    secao_funcionalidade = bool(_SECAO_FUNCIONALIDADE.search(notas))
    notas_corretivas = (
        bool(_SECAO_CORRECAO.search(notas)) and not secao_funcionalidade
    ) or itens_correcao > itens_funcionalidade
    if notas_corretivas:
        return True
    notas_com_funcionalidade = secao_funcionalidade or itens_funcionalidade > itens_correcao
    if notas_com_funcionalidade or not _patch_incrementado(tag_anterior, tag_atual):
        return False

    titulos = [mensagem.splitlines()[0] for mensagem in mensagens if mensagem]
    titulos = [titulo for titulo in titulos if not _COMMIT_DE_RELEASE.match(titulo)]
    commits_correcao = sum(bool(_CORRECAO.search(titulo)) for titulo in titulos)
    commits_funcionalidade = sum(bool(_FUNCIONALIDADE.search(titulo)) for titulo in titulos)
    return commits_correcao >= commits_funcionalidade


HEURISTICAS: dict[str, Callable[..., bool]] = {
    "v1": lambda anterior, atual, mensagens, notas=None: release_corretiva(anterior, atual, mensagens),
    "v2": release_corretiva_v2,
}


def classificar_comparacoes(
    comparacoes: list[dict],
    notas: dict[str, str | None] | None = None,
    versao: str = VERSAO_ATUAL,
) -> dict[str, bool]:
    """Classifica as releases que possuem comparação entre tags coletada.

    `notas` mapeia tag -> corpo da release (usado a partir da v2)."""
    heuristica = HEURISTICAS[versao]
    notas = notas or {}
    return {
        comparacao["tag_release"]: heuristica(
            comparacao.get("tag_anterior"),
            comparacao.get("tag_release"),
            [commit.get("message") for commit in comparacao.get("commits", [])],
            notas.get(comparacao["tag_release"]),
        )
        for comparacao in comparacoes
        if comparacao.get("tag_release")
    }


def notas_por_tag(releases: list[dict]) -> dict[str, str | None]:
    return {release["tag_name"]: release.get("body") for release in releases if release.get("tag_name")}
