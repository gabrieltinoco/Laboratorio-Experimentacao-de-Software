"""Exporta os rótulos de uma planilha independente para CSV em formato longo.

Uso: python -m validacao.exportar_rotulos --planilha validacao/rotulos_avaliador_1.xlsx --saida validacao/rotulos_B.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from validacao.rotulos import ABA_RELEASES, ABA_REPOSITORIOS, ler_rotulos, problemas_de_preenchimento

COLUNAS = [
    "repositorio",
    "tipo_projeto",
    "entregas_reais",
    "observacoes_repositorio",
    "tag_name",
    "publicada_em",
    "link_release",
    "link_commits",
    "corretiva",
    "observacoes_release",
]


def exportar(caminho_planilha: str | Path, caminho_saida: str | Path) -> pd.DataFrame:
    """Valida a planilha e exporta uma linha por release, preservando os rótulos."""
    abas = ler_rotulos(caminho_planilha)
    problemas = problemas_de_preenchimento(abas)
    if problemas:
        raise ValueError(
            "A planilha contém rótulos vazios ou inválidos: " + "; ".join(problemas)
        )

    repositorios = abas[ABA_REPOSITORIOS]
    releases = abas[ABA_RELEASES]
    if repositorios["repositorio"].duplicated().any():
        raise ValueError("A planilha contém repositórios duplicados.")
    if releases.duplicated(["repositorio", "tag_name"]).any():
        raise ValueError("A planilha contém releases duplicadas.")

    repositorios = repositorios.rename(
        columns={"observacoes": "observacoes_repositorio"}
    )
    releases = releases.rename(columns={"observacoes": "observacoes_release"})
    resultado = releases.merge(
        repositorios[
            ["repositorio", "tipo_projeto", "entregas_reais", "observacoes_repositorio"]
        ],
        on="repositorio",
        how="left",
        validate="many_to_one",
        indicator=True,
    )
    sem_repositorio = resultado["_merge"] != "both"
    if sem_repositorio.any():
        raise ValueError(
            f"{int(sem_repositorio.sum())} release(s) não têm rótulo de repositório."
        )

    resultado = resultado[COLUNAS]
    destino = Path(caminho_saida)
    destino.parent.mkdir(parents=True, exist_ok=True)
    resultado.to_csv(destino, index=False, encoding="utf-8")
    return resultado


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Exporta rótulos independentes para CSV, sem alterar a planilha."
    )
    parser.add_argument("--planilha", required=True, help="Planilha .xlsx já preenchida.")
    parser.add_argument("--saida", required=True, help="Caminho do CSV de saída.")
    args = parser.parse_args(argv)
    resultado = exportar(args.planilha, args.saida)
    print(f"{len(resultado)} releases exportadas para {args.saida}.")


if __name__ == "__main__":
    main()
