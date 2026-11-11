"""Motor de simulacao: taxa de rejeicao em 10.000 repeticoes (Q1, Q2 e Q3).

Formato de saida (results/q1_q2_q3.csv), combinado com o Integrante B:
    pergunta, situacao, teste, efeito, n_por_grupo, n_rep,
    taxa_rejeicao, ic95_inf, ic95_sup

Uso: python -m src.experimentos   # seed 42; grava results/q1_q2_q3.csv
                                  # e results/q1_q2_q3_alpha001.csv
"""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pandas as pd

from src.cenarios_q3 import SITUACOES
from src.simulacao import gerar_dados
from src.testes import teste_mann_whitney, teste_welch

RAIZ = Path(__file__).resolve().parent.parent
ARQ_RESULTADOS = RAIZ / "results" / "q1_q2_q3.csv"
ARQ_RESULTADOS_ALPHA001 = RAIZ / "results" / "q1_q2_q3_alpha001.csv"

COLUNAS = [
    "pergunta",
    "situacao",
    "teste",
    "efeito",
    "n_por_grupo",
    "n_rep",
    "taxa_rejeicao",
    "ic95_inf",
    "ic95_sup",
]

TESTES = {"welch": teste_welch, "mann_whitney": teste_mann_whitney}

N_BASE = 30
N_REP = 10_000
ALPHA = 0.05
# Com sigma = 2,23 a lognormal e tao dispersa que efeitos ate 0,5 dao pouco
# poder com n = 30; a grade vai ate 0,9 para a curva chegar perto de 100%.
EFEITOS = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]

# Valores gerados por bloco (n_rep x 2n). Acima disso a grade e dividida em
# blocos de repeticoes para nao estourar a memoria com n grande.
_MAX_VALORES_BLOCO = 2_000_000


def _ic95(taxa: float, n_rep: int) -> tuple[float, float]:
    ep = np.sqrt(taxa * (1 - taxa) / n_rep)
    return max(taxa - 1.96 * ep, 0.0), min(taxa + 1.96 * ep, 1.0)


def _p_valores(gerador, testes, efeito, n, rng, n_rep, params, tamanho_bloco=None):
    """p-valores de cada teste, aplicados aos MESMOS n_rep conjuntos simulados.

    Gera as amostras com shape (bloco, n) e chama os testes vetorizados
    (axis=-1): nao ha laco sobre as repeticoes, so sobre blocos grandes.
    """
    if tamanho_bloco is None:
        tamanho_bloco = max(1, _MAX_VALORES_BLOCO // (2 * n))
    partes = {nome: [] for nome in testes}
    feitas = 0
    while feitas < n_rep:
        m = min(tamanho_bloco, n_rep - feitas)
        a, b = gerador(n=n, efeito=efeito, rng=rng, n_rep=m, **params)
        for nome, teste in testes.items():
            partes[nome].append(np.atleast_1d(teste(a, b)["p_valor"]))
        feitas += m
    return {nome: np.concatenate(p) for nome, p in partes.items()}


def taxa_rejeicao(gerador, teste, efeito, n, rng, n_rep=N_REP, alpha=ALPHA, **params):
    """Proporcao de p < alpha em n_rep repeticoes, com IC 95% (Wald)."""
    p = _p_valores(gerador, {"t": teste}, efeito, n, rng, n_rep, params)["t"]
    taxa = float(np.mean(p < alpha))
    return (taxa, *_ic95(taxa, n_rep))


def rodar_grade(
    geradores,
    testes,
    efeitos,
    n,
    rng,
    n_rep=N_REP,
    alpha=ALPHA,
    pergunta="",
    params=None,
    tamanho_bloco=None,
) -> pd.DataFrame:
    """Taxa de rejeicao para cada gerador x efeito x teste, no formato do CSV.

    geradores: {situacao: gerador}; testes: {nome: funcao de src.testes}.
    params: mediana e sigma da simulacao (default: ajustados aos dados reais).
    """
    if params is None:
        from src.parametros import parametros_simulacao

        params = parametros_simulacao()
    linhas = []
    for situacao, gerador in geradores.items():
        for efeito in efeitos:
            pvals = _p_valores(gerador, testes, efeito, n, rng, n_rep, params, tamanho_bloco)
            for nome, p in pvals.items():
                taxa = float(np.mean(p < alpha))
                inf, sup = _ic95(taxa, n_rep)
                linhas.append(
                    {
                        "pergunta": pergunta,
                        "situacao": situacao,
                        "teste": nome,
                        "efeito": float(efeito),
                        "n_por_grupo": int(n),
                        "n_rep": int(n_rep),
                        "taxa_rejeicao": taxa,
                        "ic95_inf": inf,
                        "ic95_sup": sup,
                    }
                )
    return pd.DataFrame(linhas, columns=COLUNAS)


def rodar_todas(rng, n_rep=N_REP, efeitos=EFEITOS, params=None, alpha=ALPHA) -> pd.DataFrame:
    """Q1 (H0 verdadeira), Q2 (curva de poder) e Q3 (Q1 e Q2 em cada situacao)."""
    if params is None:
        from src.parametros import parametros_simulacao

        params = parametros_simulacao()
    comum = dict(testes=TESTES, rng=rng, n_rep=n_rep, alpha=alpha, params=params)
    partes = [
        rodar_grade({"base": gerar_dados}, efeitos=[0.0], n=N_BASE, pergunta="Q1", **comum),
        rodar_grade({"base": gerar_dados}, efeitos=efeitos, n=N_BASE, pergunta="Q2", **comum),
    ]
    for nome, sit in SITUACOES.items():
        partes.append(
            rodar_grade({nome: sit["gerador"]}, efeitos=efeitos, n=sit["n"], pergunta="Q3", **comum)
        )
    return pd.concat(partes, ignore_index=True)


def _salvar(df: pd.DataFrame, caminho: Path) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    df.round({"taxa_rejeicao": 4, "ic95_inf": 4, "ic95_sup": 4}).to_csv(caminho, index=False)


def resumo(df: pd.DataFrame) -> str:
    """Tabela larga: erro tipo I (efeito 0) e poder, por situacao e teste."""
    tabela = df[df["pergunta"] != "Q1"].pivot_table(
        index=["situacao", "efeito"], columns="teste", values="taxa_rejeicao"
    )
    q1 = df[df["pergunta"] == "Q1"].set_index("teste")["taxa_rejeicao"]
    return (
        f"Q1 (base, efeito 0): welch = {q1['welch']:.4f}, mann_whitney = {q1['mann_whitney']:.4f}\n"
        + tabela.round(4).to_string()
    )


def main() -> None:
    rng = np.random.default_rng(42)
    inicio = time.perf_counter()
    df = rodar_todas(rng)
    _salvar(df, ARQ_RESULTADOS)
    print(f"Gravado {ARQ_RESULTADOS.relative_to(RAIZ)} ({len(df)} linhas)")
    print(resumo(df))

    df_001 = rodar_todas(rng, alpha=0.01)
    _salvar(df_001, ARQ_RESULTADOS_ALPHA001)
    print(f"\nGravado {ARQ_RESULTADOS_ALPHA001.relative_to(RAIZ)} (alpha = 0,01)")
    print(resumo(df_001))
    print(f"\nTempo total: {time.perf_counter() - inicio:.1f} s")


if __name__ == "__main__":
    main()
