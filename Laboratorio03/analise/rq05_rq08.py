"""RQ 05 (frequência x CFR, Spearman) e bônus RQ 08 (rework rate x CFR (b)).

Uso: python -m analise.rq05_rq08 [--dados dados/repositorios.csv]
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import spearmanr, wilcoxon

from analise.comum import COR_SERIE, argumentos, estilo, ler_dataset, salvar_figura, salvar_tabela, tabela_resumo

PARES_RQ05 = {
    "cfr_ci": "CFR (a) proxy de CI",
    "cfr_releases": "CFR (b) proxy de entrega",
}


def correlacao(df: pd.DataFrame, x: str, y: str) -> dict:
    pares = df[[x, y]].dropna()
    rho, p = spearmanr(pares[x], pares[y])
    return {"x": x, "y": y, "rho": rho, "p_valor": p, "n": len(pares)}


def spearman_rq05(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame([correlacao(df, "deploy_freq_semana", cfr) for cfr in PARES_RQ05])


def rework_vs_cfr(df: pd.DataFrame) -> pd.DataFrame:
    """Rework conta corretivas; CFR (b) conta releases seguidas por corretiva em 7 dias.

    O Wilcoxon pareado testa se as duas proporções diferem no mesmo repositório.
    """
    pares = df[["rework_rate", "cfr_releases"]].dropna()
    diferenca = pares["rework_rate"] - pares["cfr_releases"]
    teste = wilcoxon(pares["rework_rate"], pares["cfr_releases"]) if diferenca.any() else None
    return pd.DataFrame([{
        "n": len(pares),
        "diferenca_mediana": diferenca.median(),
        "pct_rework_maior": 100 * (diferenca > 0).mean(),
        "pct_iguais": 100 * (diferenca == 0).mean(),
        "pct_rework_menor": 100 * (diferenca < 0).mean(),
        "wilcoxon_p_valor": None if teste is None else teste.pvalue,
        **{f"spearman_{k}": v for k, v in correlacao(pares, "rework_rate", "cfr_releases").items()
           if k in ("rho", "p_valor")},
    }])


def figura_rq05(df: pd.DataFrame, correlacoes: pd.DataFrame):
    figura, eixos = plt.subplots(1, 2, figsize=(9, 3.4), sharex=True)
    for eixo, (cfr, rotulo), cor in zip(eixos, PARES_RQ05.items(), COR_SERIE):
        pares = df[["deploy_freq_semana", cfr]].dropna()
        eixo.scatter(pares["deploy_freq_semana"], pares[cfr], s=14, color=cor, alpha=0.6,
                     edgecolors="white", linewidths=0.5)
        eixo.set_xscale("log")
        eixo.set_xlabel("frequência de deploy (releases/semana, log)")
        eixo.set_ylabel(rotulo)
        linha = correlacoes.set_index("y").loc[cfr]
        eixo.set_title(f"ρ = {linha['rho']:.2f}, p = {linha['p_valor']:.3g}, n = {int(linha['n'])}")
    figura.tight_layout()
    return figura


def figura_rq08(df: pd.DataFrame):
    pares = df[["rework_rate", "cfr_releases"]].dropna()
    figura, eixo = plt.subplots(figsize=(4.2, 4))
    eixo.plot([0, 1], [0, 1], color="#a8a7a2", linewidth=1, linestyle="--", label="rework = CFR (b)")
    eixo.scatter(pares["cfr_releases"], pares["rework_rate"], s=14, color=COR_SERIE[0], alpha=0.6,
                 edgecolors="white", linewidths=0.5)
    eixo.set_xlim(-0.02, 1.02)
    eixo.set_ylim(-0.02, 1.02)
    eixo.set_xlabel("CFR (b)")
    eixo.set_ylabel("rework rate")
    eixo.legend(loc="upper left")
    return figura


def main(argv: list[str] | None = None) -> None:
    args = argumentos("RQ 05 e RQ 08: frequência x CFR e rework rate.", argv)
    saidas = Path(args.saidas)
    df = ler_dataset(args.dados)
    estilo()

    correlacoes = spearman_rq05(df)
    salvar_tabela(correlacoes, "rq05_spearman", saidas)
    salvar_figura(figura_rq05(df, correlacoes), "rq05_dispersao", saidas)

    salvar_tabela(tabela_resumo(df, {"rework_rate": "rework rate", "cfr_releases": "CFR (b)"}),
                  "rq08_resumo", saidas)
    salvar_tabela(rework_vs_cfr(df), "rq08_rework_vs_cfr", saidas)
    salvar_figura(figura_rq08(df), "rq08_rework_vs_cfr", saidas)


if __name__ == "__main__":
    main()
