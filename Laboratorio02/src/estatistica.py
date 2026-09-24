"""
Funcoes estatisticas compartilhadas pela analise da S03 (RQ1, RQ2 e RQ3).

O desenho e crossover within-subject: cada integrante resolve metade das katas
com IA e metade sem IA, e nenhuma kata e repetida pelo mesmo integrante. Por
isso o par usado no Wilcoxon e o INTEGRANTE: para cada um, a mediana dos seus
trials com_ia e comparada com a mediana dos seus trials sem_ia. Parear por
(integrante, kata) nao e possivel, porque cada kata so aparece em um tratamento
para um mesmo integrante.

Seguindo o enunciado, a estatistica descritiva usa mediana e IQR (nao media e
desvio-padrao) e outliers sao apenas sinalizados, nunca descartados.
"""

from __future__ import annotations

import math

import pandas as pd
from scipy import stats

TRATAMENTOS = ("com_ia", "sem_ia")
ALPHA = 0.05


def descritiva(df: pd.DataFrame, metricas: list[str]) -> pd.DataFrame:
    """Mediana, quartis, IQR, minimo, maximo e n de cada metrica por tratamento."""
    linhas = []
    for metrica in metricas:
        for tratamento in TRATAMENTOS:
            valores = df.loc[df["tratamento"] == tratamento, metrica].dropna()
            q1, q3 = (valores.quantile(0.25), valores.quantile(0.75)) if len(valores) else (math.nan, math.nan)
            linhas.append({
                "metrica": metrica,
                "tratamento": tratamento,
                "n": len(valores),
                "mediana": valores.median(),
                "q1": q1,
                "q3": q3,
                "iqr": q3 - q1,
                "minimo": valores.min(),
                "maximo": valores.max(),
                "media": valores.mean(),
            })
    return pd.DataFrame(linhas)


def outliers_iqr(df: pd.DataFrame, metricas: list[str]) -> pd.DataFrame:
    """Sinaliza trials fora das cercas de Tukey (Q1 - 1,5*IQR, Q3 + 1,5*IQR).

    As cercas sao calculadas dentro de cada tratamento: os dois tratamentos tem
    distribuicoes diferentes por hipotese, e cercas comuns marcariam como
    outlier justamente o efeito que se quer medir.
    """
    linhas = []
    for metrica in metricas:
        for tratamento in TRATAMENTOS:
            grupo = df[df["tratamento"] == tratamento]
            valores = grupo[metrica].dropna()
            if len(valores) < 4:
                continue
            q1, q3 = valores.quantile(0.25), valores.quantile(0.75)
            iqr = q3 - q1
            baixo, alto = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            fora = grupo[(grupo[metrica] < baixo) | (grupo[metrica] > alto)]
            for _, trial in fora.iterrows():
                linhas.append({
                    "metrica": metrica,
                    "tratamento": tratamento,
                    "trial_id": trial["trial_id"],
                    "integrante": trial["integrante"],
                    "kata": trial["kata"],
                    "valor": trial[metrica],
                    "cerca_inferior": round(baixo, 4),
                    "cerca_superior": round(alto, 4),
                })
    return pd.DataFrame(linhas, columns=[
        "metrica", "tratamento", "trial_id", "integrante", "kata", "valor", "cerca_inferior", "cerca_superior",
    ])


def pares_por_integrante(df: pd.DataFrame, metricas: list[str]) -> pd.DataFrame:
    """Uma linha por integrante com a mediana de cada metrica em cada tratamento.

    Integrantes sem trials nos dois tratamentos ficam de fora, porque nao formam
    par.
    """
    medianas = df.groupby(["integrante", "tratamento"])[metricas].median().unstack("tratamento")
    medianas.columns = [f"{metrica}_{tratamento}" for metrica, tratamento in medianas.columns]
    colunas = [f"{m}_{t}" for m in metricas for t in TRATAMENTOS]
    medianas = medianas.reindex(columns=colunas)
    for metrica in metricas:
        medianas[f"{metrica}_diferenca"] = medianas[f"{metrica}_com_ia"] - medianas[f"{metrica}_sem_ia"]
    return medianas.reset_index()


def wilcoxon_pareado(pares: pd.DataFrame, metrica: str, alternativa_h1: str) -> dict:
    """Wilcoxon signed-rank pareado (com_ia - sem_ia) e tamanho de efeito.

    alternativa_h1 e a direcao da H1 do desenho ("less" = menor com IA,
    "two-sided" = difere). O p-valor bilateral e sempre reportado porque o
    desenho fixou o teste bilateral com alpha = 0,05; o unilateral aparece como
    complemento quando a H1 e direcional.

    O tamanho de efeito e a correlacao rank-biserial pareada:
    r = (W+ - W-) / (W+ + W-), em [-1, 1]. Negativo indica valores menores com
    IA.
    """
    dados = pares[[f"{metrica}_com_ia", f"{metrica}_sem_ia"]].dropna()
    com, sem = dados[f"{metrica}_com_ia"], dados[f"{metrica}_sem_ia"]
    diferencas = com - sem
    nao_nulas = diferencas[diferencas != 0]

    resultado = {
        "metrica": metrica,
        "n_pares": len(dados),
        "n_pares_nao_nulos": len(nao_nulas),
        "mediana_com_ia": com.median(),
        "mediana_sem_ia": sem.median(),
        "mediana_diferenca": diferencas.median(),
        "W": math.nan,
        "p_bilateral": math.nan,
        "p_unilateral": math.nan,
        "rank_biserial": math.nan,
        "rejeita_h0": False,
        "observacao": "",
    }

    if len(nao_nulas) == 0:
        resultado["observacao"] = "todas as diferencas sao zero; teste nao aplicavel (nao ha evidencia de diferenca)"
        return resultado

    # Com n pares nao nulos, o menor p bilateral possivel e 2 / 2^n. Abaixo de
    # 6 pares ele nunca fica abaixo de 0,05, e o teste nao tem como rejeitar H0.
    p_minimo = 2 / 2 ** len(nao_nulas)
    if p_minimo > ALPHA:
        resultado["observacao"] = (
            f"apenas {len(nao_nulas)} pares nao nulos: o menor p bilateral possivel e {p_minimo:.3f}, "
            f"logo o teste nao consegue rejeitar H0 com alpha = {ALPHA}"
        )

    bilateral = stats.wilcoxon(com, sem, alternative="two-sided")
    resultado["W"] = bilateral.statistic
    resultado["p_bilateral"] = bilateral.pvalue
    if alternativa_h1 != "two-sided":
        resultado["p_unilateral"] = stats.wilcoxon(com, sem, alternative=alternativa_h1).pvalue

    postos = stats.rankdata(nao_nulas.abs())
    w_mais = postos[nao_nulas.to_numpy() > 0].sum()
    w_menos = postos[nao_nulas.to_numpy() < 0].sum()
    resultado["rank_biserial"] = (w_mais - w_menos) / (w_mais + w_menos)
    resultado["rejeita_h0"] = bool(bilateral.pvalue < ALPHA)
    return resultado


def fmt(valor, casas: int = 2) -> str:
    """Formata numero para as tabelas em Markdown; ausente vira '-'."""
    if valor is None or (isinstance(valor, float) and math.isnan(valor)):
        return "-"
    if isinstance(valor, float):
        return f"{valor:.{casas}f}"
    return str(valor)


def tabela_markdown(df: pd.DataFrame, colunas: list[str], casas: int = 2) -> str:
    cabecalho = "| " + " | ".join(colunas) + " |"
    separador = "|" + "---|" * len(colunas)
    corpo = ["| " + " | ".join(fmt(linha[c], casas) for c in colunas) + " |" for _, linha in df.iterrows()]
    return "\n".join([cabecalho, separador, *corpo])
