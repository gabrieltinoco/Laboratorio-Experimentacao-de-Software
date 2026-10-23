"""Recalcula repositorios.csv a partir das saídas já coletadas, sem chamar a API.

Uso: python -m pipeline.recalcular --config config.yaml

Lê metadados.csv, os .jsonl e coleta_resumo.json de `caminhos.dados` e refaz
apenas o cálculo das métricas (ex.: depois de trocar a versão da heurística
corretiva). A amostra e os dados coletados ficam como estão.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
import yaml

from pipeline.consolidacao import consolidar

ARQUIVOS = {
    "releases": "releases.jsonl",
    "tags": "tags.jsonl",
    "comparacoes": "commits_entre_releases.jsonl",
    "compare_404": "compare_404.jsonl",
    "workflow_runs": "workflow_runs.jsonl",
}


def carregar_coletas(pasta: Path, repositorios: list[str]) -> dict[str, dict]:
    resumo = json.loads((pasta / "coleta_resumo.json").read_text(encoding="utf-8"))
    coletas = {
        nome: {chave: [] for chave in ARQUIVOS} | {"meses_no_teto": resumo[nome]["meses_no_teto"]}
        for nome in repositorios
    }
    for chave, arquivo in ARQUIVOS.items():
        with (pasta / arquivo).open(encoding="utf-8") as entrada:
            for linha in entrada:
                registro = json.loads(linha)
                nome = registro.pop("repositorio")
                if nome in coletas:
                    coletas[nome][chave].append(registro)
    return coletas


def recalcular(pasta: Path, inicio: str, fim: str) -> pd.DataFrame:
    amostra = pd.read_csv(pasta / "metadados.csv")
    coletas = carregar_coletas(pasta, amostra["repositorio"].tolist())
    return consolidar(amostra, coletas, inicio, fim)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Recalcula as métricas sem coletar de novo.")
    parser.add_argument("--config", default="config.yaml")
    args = parser.parse_args(argv)
    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    pasta = Path(config["caminhos"]["dados"])
    repositorios = recalcular(pasta, str(config["janela"]["inicio"]), str(config["janela"]["fim"]))
    repositorios.to_csv(pasta / "repositorios.csv", index=False)
    print(f"{len(repositorios)} repositórios recalculados em {pasta / 'repositorios.csv'}")


if __name__ == "__main__":
    main()
