"""Gerador de dados simulados (lognormal) e conjunto de exemplo.

Uso: python -m src.simulacao   # grava results/exemplo_simulado.csv (seed 42)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
ARQ_EXEMPLO = RAIZ / "results" / "exemplo_simulado.csv"


def gerar_dados(n, mediana, sigma, efeito, rng, n_rep=1):
    """Gera tempos ate o merge (horas) para os grupos sem bot e com bot.

    Parametros
    ----------
    n : int
        Observacoes por grupo em cada repeticao.
    mediana : float
        Mediana do grupo sem bot, em horas.
    sigma : float
        Desvio-padrao de log(x); controla a assimetria (comum aos dois grupos).
    efeito : float
        Reducao relativa da mediana no grupo com bot. 0 = H0 verdadeira
        (as duas distribuicoes sao identicas); 0.3 = a mediana com bot e 30%
        menor (mediana * 0.7). Deve estar em [0, 1).
    rng : numpy.random.Generator
        Gerador criado no ponto de entrada (default_rng(42)). Esta funcao nao
        cria gerador proprio, para que os resultados sejam reproduziveis.
    n_rep : int
        Numero de repeticoes (conjuntos de dados) geradas de uma vez.

    Retorna
    -------
    (sem_bot, com_bot) : tuple de numpy.ndarray, cada um com shape (n_rep, n).
    """
    if not 0 <= efeito < 1:
        raise ValueError("efeito deve estar em [0, 1)")
    mu0 = np.log(mediana)
    mu1 = np.log(mediana * (1 - efeito))
    a = rng.lognormal(mu0, sigma, size=(n_rep, n))
    b = rng.lognormal(mu1, sigma, size=(n_rep, n))
    return a, b


def exemplo_simulado(rng, n=30, efeito=0.3, params=None) -> pd.DataFrame:
    """Um conjunto simulado (n por grupo) no formato longo: grupo, horas_ate_merge."""
    from src.parametros import parametros_simulacao

    p = params or parametros_simulacao()
    a, b = gerar_dados(n=n, mediana=p["mediana"], sigma=p["sigma"], efeito=efeito, rng=rng)
    return pd.DataFrame(
        {
            "grupo": ["sem_bot"] * n + ["com_bot"] * n,
            "horas_ate_merge": np.concatenate([a[0], b[0]]).round(4),
        }
    )


def main() -> None:
    rng = np.random.default_rng(42)
    df = exemplo_simulado(rng)
    ARQ_EXEMPLO.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(ARQ_EXEMPLO, index=False)
    print(f"Gravado {ARQ_EXEMPLO.relative_to(RAIZ)} ({len(df)} linhas, n = 30 por grupo, efeito = 0,3)")
    print(df.groupby("grupo")["horas_ate_merge"].describe().round(2).to_string())


if __name__ == "__main__":
    main()
