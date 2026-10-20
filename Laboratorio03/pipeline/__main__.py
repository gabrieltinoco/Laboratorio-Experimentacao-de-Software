"""Pipeline completo: selecao, coleta de releases/runs e calculo das metricas.

Uso: python -m pipeline --config config.yaml
Subamostra: python -m pipeline --config config.yaml --repos lista.txt --saida dados_replicacao
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd
import yaml

from pipeline.coleta import ColetorRepositorio
from pipeline.consolidacao import consolidar
from pipeline.http_client import GitHubClient
from pipeline.selecao import selecionar

ETAPA_INCLUSAO = "mínimo de releases e workflow runs"


def ler_lista(caminho: str | Path) -> list[str]:
    """Um `dono/nome` por linha; linhas vazias e comentarios (#) sao ignorados."""
    linhas = Path(caminho).read_text(encoding="utf-8").splitlines()
    return [linha.strip() for linha in linhas if linha.strip() and not linha.lstrip().startswith("#")]


def executar(config: dict, cliente: GitHubClient, repositorios: list[str] | None = None) -> pd.DataFrame:
    """Roda todas as etapas e grava as saidas em `caminhos.dados`."""
    pasta = Path(config["caminhos"]["dados"])
    inicio, fim = str(config["janela"]["inicio"]), str(config["janela"]["fim"])

    coletor = ColetorRepositorio(config)
    amostra, funil = selecionar(
        cliente, config, criterios=[(ETAPA_INCLUSAO, coletor)], repositorios=repositorios
    )
    repositorios = consolidar(amostra, coletor.coletas, inicio, fim)

    pasta.mkdir(parents=True, exist_ok=True)
    amostra.to_csv(pasta / "metadados.csv", index=False)
    funil.salvar(pasta)
    coletor.salvar(pasta)
    repositorios.to_csv(pasta / "repositorios.csv", index=False)
    print(funil.tabela().to_string(index=False))
    return repositorios


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Coleta e calcula as metricas DORA da amostra.")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--repos", help="arquivo com um dono/nome por linha; pula a busca")
    parser.add_argument("--saida", help="pasta das saidas no lugar de caminhos.dados")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    if args.saida:
        config["caminhos"]["dados"] = args.saida
    repositorios = ler_lista(args.repos) if args.repos else None
    executar(config, GitHubClient.from_config(config), repositorios)


if __name__ == "__main__":
    main()
