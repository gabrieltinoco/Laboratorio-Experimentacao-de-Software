"""Concordancia entre os avaliadores da amostra-ouro e lista de divergencias para o consenso.

Uso: python -m validacao.concordancia --config config.yaml

Com dois avaliadores a medida principal e o kappa de Cohen; o kappa de Fleiss
tambem e reportado (com dois avaliadores ele difere pouco do Cohen).
Saidas na pasta da validacao:
- concordancia.csv: kappa e concordancia observada por dimensao;
- divergencias.csv: itens em que os avaliadores discordaram, com as colunas
  rotulo_consenso e motivo para preencher na reuniao de consenso. Decisoes ja
  registradas sao preservadas quando o script roda de novo.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from sklearn.metrics import cohen_kappa_score
from statsmodels.stats.inter_rater import aggregate_raters, fleiss_kappa

from validacao.rotulos import (
    ABA_RELEASES,
    CHAVES,
    DIMENSOES,
    caminho_rotulos,
    ler_rotulos,
    problemas_de_preenchimento,
)

COLUNAS_DIVERGENCIA = ["dimensao", "repositorio", "tag_name"]

# Landis & Koch (1977): limite superior de cada faixa a partir de 0.
FAIXAS_LANDIS_KOCH = [(0.20, "leve"), (0.40, "razoável"), (0.60, "moderada"), (0.80, "substancial")]


def landis_koch(kappa: float) -> str:
    if math.isnan(kappa):
        return "indefinido"
    if kappa < 0:
        return "pobre"
    for limite, rotulo in FAIXAS_LANDIS_KOCH:
        if kappa <= limite:
            return rotulo
    return "quase perfeita"


def kappa_cohen(a: pd.Series, b: pd.Series) -> float:
    # Kappa e indefinido (0/0) quando os dois avaliadores usam um unico rotulo igual.
    if a.nunique() == 1 and b.nunique() == 1 and a.iloc[0] == b.iloc[0]:
        return float("nan")
    return float(cohen_kappa_score(a, b))


def kappa_fleiss(rotulos: pd.DataFrame) -> float:
    """`rotulos`: uma linha por item, uma coluna por avaliador."""
    categorias = {valor: i for i, valor in enumerate(sorted(pd.unique(rotulos.to_numpy().ravel())))}
    contagens, _ = aggregate_raters(rotulos.apply(lambda coluna: coluna.map(categorias)).to_numpy())
    if contagens.shape[1] == 1:
        return float("nan")
    with np.errstate(invalid="ignore", divide="ignore"):
        return float(fleiss_kappa(contagens, method="fleiss"))


def tabela_da_dimensao(rotulos: dict[str, dict[str, pd.DataFrame]], dimensao: str) -> pd.DataFrame:
    """Itens rotulados por todos os avaliadores: chaves + uma coluna por avaliador."""
    aba, coluna, _ = DIMENSOES[dimensao]
    chaves = CHAVES[aba]
    tabela = None
    for avaliador, abas in rotulos.items():
        parte = abas[aba][chaves + [coluna]].rename(columns={coluna: avaliador})
        tabela = parte if tabela is None else tabela.merge(parte, on=chaves, how="inner")
    tabela = tabela.reset_index(drop=True)
    if aba != ABA_RELEASES:
        tabela["tag_name"] = ""
    return tabela


def comparar(rotulos: dict[str, dict[str, pd.DataFrame]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    avaliadores = list(rotulos)
    resumo, divergencias = [], []
    for dimensao in DIMENSOES:
        tabela = tabela_da_dimensao(rotulos, dimensao)
        valores = tabela[avaliadores]
        concordam = valores.nunique(axis=1) == 1
        cohen = kappa_cohen(valores.iloc[:, 0], valores.iloc[:, 1]) if len(avaliadores) == 2 else float("nan")
        fleiss = kappa_fleiss(valores)
        resumo.append({
            "dimensao": dimensao,
            "itens": len(tabela),
            "concordancia_observada": round(float(concordam.mean()), 4),
            "kappa_cohen": round(cohen, 4),
            "kappa_fleiss": round(fleiss, 4),
            "interpretacao": landis_koch(cohen if len(avaliadores) == 2 else fleiss),
        })
        for _, linha in tabela[~concordam].iterrows():
            divergencias.append({
                "dimensao": dimensao,
                "repositorio": linha["repositorio"],
                "tag_name": linha["tag_name"],
                **{f"rotulo_{a}": linha[a] for a in avaliadores},
                "rotulo_consenso": "",
                "motivo": "",
            })
    colunas = COLUNAS_DIVERGENCIA + [f"rotulo_{a}" for a in avaliadores] + ["rotulo_consenso", "motivo"]
    return pd.DataFrame(resumo), pd.DataFrame(divergencias, columns=colunas)


def preservar_decisoes(novas: pd.DataFrame, anteriores: pd.DataFrame) -> pd.DataFrame:
    """Reaproveita rotulo_consenso e motivo ja preenchidos para os mesmos itens."""
    decididas = anteriores[COLUNAS_DIVERGENCIA + ["rotulo_consenso", "motivo"]].fillna("")
    resultado = novas.drop(columns=["rotulo_consenso", "motivo"]).merge(
        decididas, on=COLUNAS_DIVERGENCIA, how="left")
    resultado[["rotulo_consenso", "motivo"]] = resultado[["rotulo_consenso", "motivo"]].fillna("")
    return resultado[novas.columns]


def carregar_rotulos(config: dict) -> dict[str, dict[str, pd.DataFrame]]:
    """Le a planilha de cada avaliador; aborta se alguma estiver incompleta."""
    pasta = config["validacao"]["pasta"]
    rotulos, problemas = {}, []
    for avaliador in config["validacao"]["avaliadores"]:
        abas = ler_rotulos(caminho_rotulos(pasta, avaliador))
        problemas += [f"{avaliador}: {p}" for p in problemas_de_preenchimento(abas)]
        rotulos[avaliador] = abas
    if problemas:
        raise ValueError("Planilhas incompletas:\n" + "\n".join(problemas[:50]))
    return rotulos


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Kappa entre avaliadores e divergencias para o consenso.")
    parser.add_argument("--config", default="config.yaml")
    args = parser.parse_args(argv)
    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    pasta = Path(config["validacao"]["pasta"])

    resumo, divergencias = comparar(carregar_rotulos(config))
    arquivo_divergencias = pasta / "divergencias.csv"
    if arquivo_divergencias.exists():
        divergencias = preservar_decisoes(divergencias, pd.read_csv(arquivo_divergencias, dtype=str))
    resumo.to_csv(pasta / "concordancia.csv", index=False)
    divergencias.to_csv(arquivo_divergencias, index=False)

    print(resumo.to_string(index=False))
    pendentes = (divergencias["rotulo_consenso"] == "").sum()
    print(f"\n{len(divergencias)} divergencias ({pendentes} sem decisao) em {arquivo_divergencias}")


if __name__ == "__main__":
    main()
