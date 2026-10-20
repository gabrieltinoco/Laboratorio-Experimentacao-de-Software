"""Base comum das análises da S03: leitura do dataset, resumos, classificação DORA e saídas.

Uso: python -m analise.comum [--dados dados/repositorios.csv]
Gera analise/saidas/classificacao_c1.csv, usado pelas demais análises.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from metricas.classificacao import (
    CATEGORIAS,
    classificar_cfr,
    classificar_frequencia,
    classificar_geral,
    classificar_lead_time,
    classificar_recuperacao,
)

RAIZ = Path(__file__).resolve().parents[1]
DATASET = RAIZ / "dados" / "repositorios.csv"
SAIDAS = RAIZ / "analise" / "saidas"

# Paleta validada para daltonismo: duas séries categóricas e uma rampa sequencial
# (claro -> escuro) para as categorias DORA, que são ordinais.
COR_SERIE = ("#2a78d6", "#eb6834")
COR_CATEGORIA = {"Low": "#86b6ef", "Medium": "#3987e5", "High": "#1c5cab", "Elite": "#0d366b"}
TINTA = "#0b0b0b"
TINTA_SECUNDARIA = "#52514e"
GRADE = "#e4e3df"

def ler_dataset(caminho: str | Path = DATASET) -> pd.DataFrame:
    return pd.read_csv(caminho)


def resumo(serie: pd.Series) -> dict:
    """Mediana e IQR (Q3 − Q1) dos valores não vazios."""
    valores = serie.dropna()
    q1, mediana, q3 = valores.quantile([0.25, 0.5, 0.75]) if len(valores) else (None,) * 3
    return {
        "n": len(valores),
        "mediana": mediana,
        "q1": q1,
        "q3": q3,
        "iqr": None if q1 is None else q3 - q1,
    }


def tabela_resumo(df: pd.DataFrame, colunas: dict[str, str]) -> pd.DataFrame:
    """Uma linha por coluna do dataset; `colunas` mapeia nome da coluna -> rótulo."""
    return pd.DataFrame([{"metrica": rotulo, **resumo(df[coluna])} for coluna, rotulo in colunas.items()])


def _categoria(classificador, valor) -> str | None:
    return None if pd.isna(valor) else classificador(float(valor))


def classificar(
    df: pd.DataFrame,
    frequencia: str,
    lead_time: str,
    cfr: str,
    recuperacao: str = "recuperacao_horas",
) -> pd.DataFrame:
    """Categoria DORA por métrica e geral para uma combinação de definições operacionais.

    Os nomes das colunas escolhem a combinação (C1, C2, C3 da RQ 07). A geral fica
    vazia se faltar alguma das quatro categorias, como em `pipeline/consolidacao.py`.
    """
    colunas = {
        "frequencia": (frequencia, classificar_frequencia),
        "lead_time": (lead_time, classificar_lead_time),
        "cfr": (cfr, classificar_cfr),
        "recuperacao": (recuperacao, classificar_recuperacao),
    }
    saida = pd.DataFrame({"repositorio": df["repositorio"]})
    for nome, (coluna, classificador) in colunas.items():
        saida[f"categoria_{nome}"] = [_categoria(classificador, v) for v in df[coluna]]
    categorias = saida[[f"categoria_{nome}" for nome in colunas]]
    saida["categoria_geral"] = [
        None if linha.isna().any() else classificar_geral(list(linha))
        for _, linha in categorias.iterrows()
    ]
    return saida


def classificacao_c1(df: pd.DataFrame) -> pd.DataFrame:
    """C1 (referência): release, lead time (a), CFR (a)."""
    return classificar(df, "deploy_freq_semana", "lead_time_release_dias", "cfr_ci")


def distribuicao_categorias(classificacao: pd.DataFrame) -> pd.DataFrame:
    """Contagem e % de repositórios por categoria, para cada coluna `categoria_*`."""
    linhas = []
    for coluna in [c for c in classificacao.columns if c.startswith("categoria_")]:
        valores = classificacao[coluna].dropna()
        for categoria in CATEGORIAS:
            n = int((valores == categoria).sum())
            linhas.append({
                "metrica": coluna.removeprefix("categoria_"),
                "categoria": categoria,
                "n": n,
                "pct": 100 * n / len(valores) if len(valores) else None,
            })
    return pd.DataFrame(linhas)


def estilo() -> None:
    plt.rcParams.update({
        "figure.dpi": 150,
        "savefig.bbox": "tight",
        "font.size": 9,
        "axes.edgecolor": TINTA_SECUNDARIA,
        "axes.labelcolor": TINTA,
        "axes.titlesize": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": GRADE,
        "grid.linewidth": 0.6,
        "xtick.color": TINTA_SECUNDARIA,
        "ytick.color": TINTA_SECUNDARIA,
        "legend.frameon": False,
    })


def salvar_tabela(tabela: pd.DataFrame, nome: str, pasta: Path = SAIDAS) -> Path:
    """Salva em CSV (para reuso) e em Markdown (para colar no artigo)."""
    pasta.mkdir(parents=True, exist_ok=True)
    tabela.to_csv(pasta / f"{nome}.csv", index=False)
    (pasta / f"{nome}.md").write_text(tabela.astype(object).to_markdown(index=False, floatfmt=".3f") + "\n", encoding="utf-8")
    return pasta / f"{nome}.csv"


def salvar_figura(figura, nome: str, pasta: Path = SAIDAS) -> Path:
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / f"{nome}.png"
    figura.savefig(caminho)
    plt.close(figura)
    return caminho


def argumentos(descricao: str, argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=descricao)
    parser.add_argument("--dados", default=str(DATASET), help="CSV consolidado do pipeline")
    parser.add_argument("--saidas", default=str(SAIDAS), help="pasta das tabelas e figuras")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = argumentos("Classificação DORA de referência (C1).", argv)
    salvar_tabela(classificacao_c1(ler_dataset(args.dados)), "classificacao_c1", Path(args.saidas))


if __name__ == "__main__":
    main()
