"""Rotulos de consenso da amostra-ouro.

Uso: python -m validacao.consenso --config config.yaml

Itens em que os avaliadores concordaram ficam com o rotulo comum. Os demais
recebem o rotulo_consenso decidido em reuniao (validacao/divergencias.csv),
que precisa estar preenchido, com motivo, para todos os itens.
Saidas: consenso_repositorios.csv (tipo_projeto, entregas_reais; usado na RQ 06)
e consenso_releases.csv (corretiva; usado na avaliacao da heuristica).
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import yaml

from validacao.concordancia import COLUNAS_DIVERGENCIA, carregar_rotulos, tabela_da_dimensao
from validacao.rotulos import ABA_RELEASES, ABA_REPOSITORIOS, CHAVES, DIMENSOES


def rotulos_da_dimensao(rotulos: dict, dimensao: str, divergencias: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Rotulo final de cada item da dimensao e a lista de pendencias da reuniao."""
    _, coluna, permitidos = DIMENSOES[dimensao]
    tabela = tabela_da_dimensao(rotulos, dimensao)
    avaliadores = list(rotulos)
    decisoes = divergencias[divergencias["dimensao"] == dimensao].set_index(["repositorio", "tag_name"])

    finais, pendencias = [], []
    for _, linha in tabela.iterrows():
        valores = set(linha[avaliadores])
        if len(valores) == 1:
            finais.append(valores.pop())
            continue
        chave = (linha["repositorio"], linha["tag_name"])
        decisao = decisoes.loc[chave] if chave in decisoes.index else None
        if decisao is None or decisao["rotulo_consenso"] not in permitidos or not decisao["motivo"]:
            pendencias.append(f"{dimensao}: {' '.join(filter(None, chave))}")
            finais.append(None)
        else:
            finais.append(decisao["rotulo_consenso"])
    tabela[coluna] = finais
    return tabela, pendencias


def consolidar(rotulos: dict, divergencias: pd.DataFrame) -> dict[str, pd.DataFrame]:
    divergencias = divergencias.fillna("").astype(str).drop_duplicates(COLUNAS_DIVERGENCIA)
    por_aba: dict[str, pd.DataFrame] = {}
    pendencias: list[str] = []
    for dimensao, (aba, coluna, _) in DIMENSOES.items():
        tabela, faltando = rotulos_da_dimensao(rotulos, dimensao, divergencias)
        pendencias += faltando
        parte = tabela[CHAVES[aba] + [coluna]]
        por_aba[aba] = parte if aba not in por_aba else por_aba[aba].merge(parte, on=CHAVES[aba])
    if pendencias:
        raise ValueError("Divergencias sem rotulo_consenso valido ou sem motivo:\n" + "\n".join(pendencias))
    return por_aba


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Gera os rotulos de consenso da amostra-ouro.")
    parser.add_argument("--config", default="config.yaml")
    args = parser.parse_args(argv)
    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    pasta = Path(config["validacao"]["pasta"])

    consenso = consolidar(carregar_rotulos(config), pd.read_csv(pasta / "divergencias.csv", dtype=str))
    consenso[ABA_REPOSITORIOS].to_csv(pasta / "consenso_repositorios.csv", index=False)
    consenso[ABA_RELEASES].to_csv(pasta / "consenso_releases.csv", index=False)
    for aba, tabela in consenso.items():
        print(f"{aba}: {len(tabela)} itens")


if __name__ == "__main__":
    main()
