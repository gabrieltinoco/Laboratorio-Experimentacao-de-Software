"""Selecao dos repositorios: busca fatiada por estrelas, filtro de Actions, metadados e funil.

Uso isolado: python -m pipeline.selecao --config config.yaml
"""

from __future__ import annotations

import argparse
import logging
import random
from datetime import date
from pathlib import Path
from typing import Callable, Iterable

import pandas as pd
import yaml

from pipeline.funil import Funil
from pipeline.http_client import ErroGitHub, GitHubClient
from pipeline.metadados import coletar_metadados

log = logging.getLogger(__name__)

TETO_DA_BUSCA = 1000

ETAPA_ACTIONS = "com GitHub Actions"
ETAPA_METADADOS = "metadados coletados"

# Criterio adicional do funil: recebe o cliente e os metadados do repositorio e
# devolve o motivo do descarte, ou None se o repositorio passa.
Criterio = Callable[[GitHubClient, dict], "str | None"]


def consulta_da_faixa(minimo: int, maximo: int | None, pushed_desde: str) -> str:
    estrelas = f"stars:>={minimo}" if maximo is None else f"stars:{minimo}..{maximo}"
    return f"{estrelas} pushed:>={pushed_desde} archived:false"


def buscar_faixa(cliente: GitHubClient, consulta: str) -> tuple[list[dict], int]:
    """Itens da busca (no maximo 1.000) e o total_count informado pela API."""
    itens: list[dict] = []
    total = 0
    for pagina in cliente.paginas("/search/repositories", {"q": consulta, "sort": "stars", "order": "desc"}):
        total = pagina.dados["total_count"]
        itens.extend(pagina.dados["items"])
        if len(itens) >= TETO_DA_BUSCA:
            break
    if total > TETO_DA_BUSCA:
        log.warning("Busca '%s' tem %d resultados; so os %d primeiros sao acessiveis.", consulta, total, TETO_DA_BUSCA)
    return itens[:TETO_DA_BUSCA], total


def buscar_candidatos(cliente: GitHubClient, faixas: Iterable, pushed_desde: str) -> tuple[list[dict], int]:
    """Candidatos sem duplicatas (um repositorio pode mudar de faixa entre consultas)."""
    vistos: dict[str, dict] = {}
    encontrados = 0
    for minimo, maximo in faixas:
        itens, total = buscar_faixa(cliente, consulta_da_faixa(minimo, maximo, pushed_desde))
        encontrados += total
        for item in itens:
            vistos.setdefault(item["full_name"], item)
    return list(vistos.values()), encontrados


def ordem_de_avaliacao(candidatos: list[dict], semente: int) -> list[dict]:
    """Ordem aleatoria reproduzivel, para a amostra nao ficar enviesada para os mais populares."""
    ordenados = sorted(candidatos, key=lambda c: c["full_name"].lower())
    random.Random(semente).shuffle(ordenados)
    return ordenados


def contar_workflows(cliente: GitHubClient, nome: str) -> int:
    return cliente.get(f"/repos/{nome}/actions/workflows", {"per_page": 1}).dados["total_count"]


def selecionar(
    cliente: GitHubClient,
    config: dict,
    criterios: Iterable[tuple[str, Criterio]] = (),
) -> tuple[pd.DataFrame, Funil]:
    """Avalia os candidatos ate a amostra atingir `selecao.max_repositorios`.

    `criterios` sao etapas extras do funil, aplicadas depois dos metadados, na
    ordem dada (ex.: minimo de releases e de workflow runs na janela).
    """
    selecao = config["selecao"]
    inicio = str(config["janela"]["inicio"])
    referencia = date.fromisoformat(str(config["janela"]["fim"]))
    criterios = list(criterios)

    candidatos, encontrados = buscar_candidatos(cliente, selecao["faixas_estrelas"], inicio)
    funil = Funil(
        etapas=[ETAPA_ACTIONS, ETAPA_METADADOS, *(nome for nome, _ in criterios)],
        encontrados_na_busca=encontrados,
        candidatos=len(candidatos),
    )

    amostra: list[dict] = []
    for item in ordem_de_avaliacao(candidatos, selecao.get("semente", 42)):
        if len(amostra) >= selecao["max_repositorios"]:
            break
        repositorio = avaliar(cliente, item, referencia, criterios, funil)
        if repositorio is not None:
            amostra.append(repositorio)
            funil.aprovar(repositorio["repositorio"])
            log.info("Amostra: %d/%d (%s)", len(amostra), selecao["max_repositorios"], item["full_name"])

    return pd.DataFrame(amostra), funil


def avaliar(cliente: GitHubClient, item: dict, referencia: date,
            criterios: list[tuple[str, Criterio]], funil: Funil) -> dict | None:
    """Passa um candidato pelas etapas; erros 4xx descartam, falhas de rede interrompem a coleta."""
    nome = item["full_name"]
    try:
        n_workflows = contar_workflows(cliente, nome)
    except ErroGitHub as erro:
        if not erro.status:
            raise
        funil.descartar(nome, ETAPA_ACTIONS, f"erro ao listar workflows (HTTP {erro.status})")
        return None
    if n_workflows == 0:
        funil.descartar(nome, ETAPA_ACTIONS, "sem workflows")
        return None

    try:
        repositorio = coletar_metadados(cliente, item, referencia)
    except ErroGitHub as erro:
        if not erro.status:
            raise
        funil.descartar(nome, ETAPA_METADADOS, f"erro ao coletar metadados (HTTP {erro.status})")
        return None
    repositorio["workflows"] = n_workflows

    for etapa, criterio in criterios:
        motivo = criterio(cliente, repositorio)
        if motivo:
            funil.descartar(nome, etapa, motivo)
            return None
    return repositorio


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Seleciona repositorios e gera o funil.")
    parser.add_argument("--config", default="config.yaml")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    pasta = Path(config["caminhos"]["dados"])
    amostra, funil = selecionar(GitHubClient.from_config(config), config)

    pasta.mkdir(parents=True, exist_ok=True)
    amostra.to_csv(pasta / "metadados.csv", index=False)
    funil.salvar(pasta)
    print(funil.tabela().to_string(index=False))


if __name__ == "__main__":
    main()
