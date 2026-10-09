"""Pipeline completo: selecao, coleta de releases/runs e calculo das metricas.

Uso: python -m pipeline --config config.yaml
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


def executar(config: dict, cliente: GitHubClient) -> pd.DataFrame:
    """Roda todas as etapas e grava as saidas em `caminhos.dados`."""
    pasta = Path(config["caminhos"]["dados"])
    inicio, fim = str(config["janela"]["inicio"]), str(config["janela"]["fim"])

    coletor = ColetorRepositorio(config)
    amostra, funil = selecionar(cliente, config, criterios=[(ETAPA_INCLUSAO, coletor)])
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
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    executar(config, GitHubClient.from_config(config))


if __name__ == "__main__":
    main()
