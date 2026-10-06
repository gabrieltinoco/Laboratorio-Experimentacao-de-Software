"""Metadados de cada repositorio: estrelas, linguagem, default branch, idade e contribuidores."""

from __future__ import annotations

from datetime import date, datetime

from pipeline.http_client import ErroGitHub, GitHubClient


def idade_em_anos(criado_em: str, referencia: date) -> float:
    """Idade na data de referencia (fim da janela), para nao depender do dia da coleta."""
    criacao = datetime.fromisoformat(criado_em.replace("Z", "+00:00")).date()
    return round((referencia - criacao).days / 365.25, 2)


def contar_contribuidores(cliente: GitHubClient, nome: str) -> int | None:
    """None quando o GitHub recusa listar (403 em repositorios com historico grande demais)."""
    try:
        return cliente.contar(f"/repos/{nome}/contributors", {"anon": "true"})
    except ErroGitHub as erro:
        if erro.status == 403:
            return None
        raise


def coletar_metadados(cliente: GitHubClient, item_busca: dict, referencia: date) -> dict:
    nome = item_busca["full_name"]
    return {
        "repositorio": nome,
        "url": item_busca["html_url"],
        "estrelas": item_busca["stargazers_count"],
        "linguagem": item_busca.get("language") or "",
        "default_branch": item_busca["default_branch"],
        "criado_em": item_busca["created_at"],
        "idade_anos": idade_em_anos(item_busca["created_at"], referencia),
        "contribuidores": contar_contribuidores(cliente, nome),
    }
