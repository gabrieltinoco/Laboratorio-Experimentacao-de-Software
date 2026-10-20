"""RQ 01 a RQ 04: estatística descritiva e distribuição das categorias DORA (C1).

Uso: python -m analise.rq01_04 [--dados dados/repositorios.csv]
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from analise.comum import (
    COR_CATEGORIA,
    COR_SERIE,
    TINTA,
    argumentos,
    classificacao_c1,
    distribuicao_categorias,
    estilo,
    ler_dataset,
    salvar_figura,
    salvar_tabela,
    tabela_resumo,
)
from metricas.classificacao import CATEGORIAS

METRICAS = {
    "deploy_freq_semana": "RQ01 frequência de deploy (releases/semana)",
    "lead_time_release_dias": "RQ02 lead time (a) por release (dias)",
    "lead_time_commit_dias": "RQ02 lead time (b) por commit (dias)",
    "cfr_ci": "RQ03 CFR (a) proxy de CI",
    "cfr_releases": "RQ03 CFR (b) proxy de entrega",
    "recuperacao_horas": "RQ04 tempo de recuperação (horas)",
    "proporcao_censurados": "RQ04 proporção de episódios censurados",
}

ROTULOS_CATEGORIA = {
    "frequencia": "Frequência",
    "lead_time": "Lead time (a)",
    "cfr": "CFR (a)",
    "recuperacao": "Recuperação",
    "geral": "Geral",
}


def censura(df: pd.DataFrame) -> pd.DataFrame:
    """Totais da RQ 04: episódios censurados não são descartados, são reportados."""
    episodios = df["episodios_falha"].sum()
    censurados = df["episodios_censurados"].sum()
    return pd.DataFrame([{
        "repositorios": len(df),
        "repositorios_sem_episodio": int((df["episodios_falha"] == 0).sum()),
        "repositorios_com_censura": int((df["episodios_censurados"] > 0).sum()),
        "episodios": int(episodios),
        "episodios_censurados": int(censurados),
        "pct_censurados": 100 * censurados / episodios if episodios else None,
    }])


def divergencia_lead_time(df: pd.DataFrame) -> pd.DataFrame:
    """Quanto a variante (a) se afasta da (b) no mesmo repositório."""
    pares = df[["lead_time_release_dias", "lead_time_commit_dias"]].dropna()
    razao = pares["lead_time_release_dias"] / pares["lead_time_commit_dias"].where(
        pares["lead_time_commit_dias"] > 0
    )
    return pd.DataFrame([{
        "repositorios": len(pares),
        "pct_a_maior_que_b": 100 * (pares["lead_time_release_dias"] > pares["lead_time_commit_dias"]).mean(),
        "razao_a_b_mediana": razao.median(),
        "razao_a_b_q1": razao.quantile(0.25),
        "razao_a_b_q3": razao.quantile(0.75),
    }])


def _boxplot(eixo, series: list[pd.Series], rotulos: list[str], log: bool) -> None:
    caixas = eixo.boxplot(
        [s.dropna() for s in series],
        tick_labels=rotulos,
        widths=0.5,
        patch_artist=True,
        flierprops={"marker": "o", "markersize": 3, "alpha": 0.4, "markeredgewidth": 0},
        medianprops={"color": TINTA, "linewidth": 1.5},
    )
    for caixa, cor, flier in zip(caixas["boxes"], COR_SERIE, caixas["fliers"]):
        caixa.set(facecolor=cor, alpha=0.35, edgecolor=cor, linewidth=1)
        flier.set(markerfacecolor=cor)
    if log:
        eixo.set_yscale("log")
    eixo.grid(axis="x", visible=False)


def figura_distribuicoes(df: pd.DataFrame):
    figura, eixos = plt.subplots(1, 4, figsize=(11, 3.2))

    def positivos(coluna: str) -> pd.Series:
        return df[coluna].where(df[coluna] > 0)  # zeros nao cabem na escala log

    _boxplot(eixos[0], [positivos("deploy_freq_semana")], ["releases"], log=True)
    eixos[0].set_title("RQ01 frequência (por semana)")
    _boxplot(eixos[1], [positivos("lead_time_release_dias"), positivos("lead_time_commit_dias")],
             ["(a) release", "(b) commit"], log=True)
    eixos[1].set_title("RQ02 lead time (dias)")
    _boxplot(eixos[2], [df["cfr_ci"], df["cfr_releases"]], ["(a) CI", "(b) entrega"], log=False)
    eixos[2].set_title("RQ03 change failure rate")
    _boxplot(eixos[3], [positivos("recuperacao_horas")], ["episódios"], log=True)
    eixos[3].set_title("RQ04 recuperação (horas)")
    figura.tight_layout()
    return figura


def figura_categorias(distribuicao: pd.DataFrame):
    """Barras empilhadas em %, uma por métrica, na ordem Low -> Elite."""
    figura, eixo = plt.subplots(figsize=(7, 2.8))
    metricas = list(ROTULOS_CATEGORIA)
    esquerda = pd.Series(0.0, index=metricas)
    for categoria in reversed(CATEGORIAS):
        pct = distribuicao[distribuicao["categoria"] == categoria].set_index("metrica")["pct"]
        pct = pct.reindex(metricas).fillna(0)
        eixo.barh([ROTULOS_CATEGORIA[m] for m in metricas], pct, left=esquerda,
                  color=COR_CATEGORIA[categoria], edgecolor="white", linewidth=2, label=categoria, height=0.6)
        for posicao, (valor, inicio) in enumerate(zip(pct, esquerda)):
            if valor >= 8:
                cor_texto = "white" if categoria in ("High", "Elite") else TINTA
                eixo.text(inicio + valor / 2, posicao, f"{valor:.0f}%", ha="center", va="center",
                          fontsize=8, color=cor_texto)
        esquerda += pct
    eixo.invert_yaxis()
    eixo.set_xlim(0, 100)
    eixo.set_xlabel("% dos repositórios classificados")
    eixo.grid(axis="y", visible=False)
    eixo.legend(ncol=4, loc="lower center", bbox_to_anchor=(0.5, 1.0))
    return figura


def main(argv: list[str] | None = None) -> None:
    args = argumentos("RQ 01 a RQ 04: mediana, IQR e categorias DORA.", argv)
    saidas = Path(args.saidas)
    df = ler_dataset(args.dados)
    estilo()

    salvar_tabela(tabela_resumo(df, METRICAS), "rq01_04_resumo", saidas)
    salvar_tabela(censura(df), "rq04_censura", saidas)
    salvar_tabela(divergencia_lead_time(df), "rq02_divergencia_lead_time", saidas)
    distribuicao = distribuicao_categorias(classificacao_c1(df))
    salvar_tabela(distribuicao, "rq01_04_categorias_c1", saidas)
    salvar_figura(figura_distribuicoes(df), "rq01_04_distribuicoes", saidas)
    salvar_figura(figura_categorias(distribuicao), "rq01_04_categorias_c1", saidas)


if __name__ == "__main__":
    main()
