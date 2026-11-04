"""Ajuste da lognormal aos dados reais (data/real/prs.csv).

Se X ~ Lognormal(mu, sigma), entao log(X) ~ Normal(mu, sigma). Por isso os
parametros saem direto da media e do desvio-padrao de log(horas_ate_merge):

    mu      = mean(log(x))
    sigma   = std(log(x), ddof=1)
    mediana = exp(mu)          # a mediana da lognormal e e^mu

Uso: python -m src.parametros
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

RAIZ = Path(__file__).resolve().parent.parent
ARQ_PRS = RAIZ / "data" / "real" / "prs.csv"


def carregar_prs(caminho: Path = ARQ_PRS) -> pd.DataFrame:
    return pd.read_csv(caminho)


def ajustar_por_grupo(df: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por grupo com n, mu, sigma, mediana, media e assimetria."""
    linhas = []
    for grupo, x in df.groupby("grupo")["horas_ate_merge"]:
        log_x = np.log(x.to_numpy())
        linhas.append(
            {
                "grupo": grupo,
                "n": len(x),
                "mu": log_x.mean(),
                "sigma": log_x.std(ddof=1),
                "mediana": float(np.exp(log_x.mean())),
                "mediana_amostral": float(np.median(x)),
                "media_amostral": float(np.mean(x)),
                "assimetria": float(stats.skew(x)),
                "assimetria_log": float(stats.skew(log_x)),
                "shapiro_log_p": float(stats.shapiro(log_x).pvalue),
            }
        )
    return pd.DataFrame(linhas).set_index("grupo")


def parametros_simulacao(df: pd.DataFrame | None = None) -> dict:
    """Parametros da simulacao base.

    - mediana: mediana ajustada (e^mu) do grupo SEM bot, que e a referencia;
      o efeito e aplicado como reducao relativa dessa mediana no grupo com bot.
    - sigma: media dos sigmas dos dois grupos (as duas lognormais tem a mesma
      forma, entao com efeito = 0 as distribuicoes sao identicas e H0 vale).
    """
    if df is None:
        df = carregar_prs()
    ajuste = ajustar_por_grupo(df)
    return {
        "mediana": float(ajuste.loc["sem_bot", "mediana"]),
        "sigma": float(ajuste["sigma"].mean()),
    }


def main() -> None:
    df = carregar_prs()
    ajuste = ajustar_por_grupo(df)
    pd.set_option("display.width", 140)
    print("Ajuste da lognormal por grupo (horas ate o merge):")
    print(ajuste.round(3).to_string())
    p = parametros_simulacao(df)
    print(f"\nSimulacao base: mediana = {p['mediana']:.2f} h, sigma = {p['sigma']:.3f}")


if __name__ == "__main__":
    main()
