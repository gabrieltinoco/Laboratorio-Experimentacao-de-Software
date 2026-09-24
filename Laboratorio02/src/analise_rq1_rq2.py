"""
Analise estatistica da RQ1 (tempo) e da RQ2 (defeitos) - Lab02S03, Integrante A.

Le data/trials.csv, consolida tempo e testes de todos os trials e gera:

    data/analise/rq1_rq2_trials.csv      trials com as variaveis derivadas
    data/analise/rq1_rq2_descritiva.csv  mediana, quartis e IQR por tratamento
    data/analise/rq1_rq2_outliers.csv    trials fora das cercas de Tukey
    data/analise/rq1_rq2_pares.csv       mediana por integrante em cada tratamento
    data/analise/rq1_rq2_wilcoxon.csv    Wilcoxon pareado e tamanho de efeito
    docs/analise_rq1_rq2.md              resumo legivel dos resultados

Variaveis derivadas (ver docs/desenho_experimento.md):
    - tempo_ate_verde_min: minutos ate todos os testes passarem. Trial que nao
      termina com status 'passou' e censurado no time-box (35 min) e continua na
      analise, como pede o enunciado.
    - testes_falhando: testes_total - testes_passando ao fim do trial.
    - taxa_sucesso: testes_passando / testes_total.

Uso:
    python src/analise_rq1_rq2.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from estatistica import (
    ALPHA,
    descritiva,
    fmt,
    outliers_iqr,
    pares_por_integrante,
    tabela_markdown,
    wilcoxon_pareado,
)

BASE_DIR = Path(__file__).resolve().parent.parent
TRIALS_CSV = BASE_DIR / "data" / "trials.csv"
SAIDA_DIR = BASE_DIR / "data" / "analise"
RELATORIO_MD = BASE_DIR / "docs" / "analise_rq1_rq2.md"

TIMEBOX_PADRAO_MIN = 35.0

# Metrica -> direcao da H1 no desenho do experimento.
METRICAS = {
    "tempo_ate_verde_min": "less",  # RQ1: tempo menor com IA
    "testes_falhando": "less",      # RQ2: menos testes falhando com IA
    "taxa_sucesso": "greater",      # RQ2: taxa de sucesso maior com IA
}


def carrega_trials() -> pd.DataFrame:
    df = pd.read_csv(TRIALS_CSV, dtype={"trial_id": str, "integrante": str})
    for coluna in ("tempo_minutos", "timebox_minutos", "testes_passando", "testes_total"):
        df[coluna] = pd.to_numeric(df[coluna], errors="coerce")

    timebox = df["timebox_minutos"].fillna(TIMEBOX_PADRAO_MIN)
    df["censurado"] = df["status"] != "passou"
    df["tempo_ate_verde_min"] = df["tempo_minutos"].where(~df["censurado"], timebox)

    df["testes_falhando"] = df["testes_total"] - df["testes_passando"]
    df["taxa_sucesso"] = (df["testes_passando"] / df["testes_total"]).where(df["testes_total"] > 0)
    return df


def gera_relatorio(df: pd.DataFrame, desc: pd.DataFrame, outliers: pd.DataFrame, testes: pd.DataFrame) -> str:
    n_integrantes = df["integrante"].nunique()
    n_censurados = int(df["censurado"].sum())
    por_tratamento = df.groupby("tratamento").size().to_dict()

    sucesso_total = (
        df.assign(todos_passaram=df["testes_falhando"] == 0)
        .groupby("tratamento")["todos_passaram"].mean()
        .mul(100)
    )

    linhas = [
        "# Análise RQ1 (tempo) e RQ2 (defeitos)",
        "",
        "> Arquivo gerado por [`src/analise_rq1_rq2.py`](../src/analise_rq1_rq2.py). "
        "Não editar à mão: rode o script de novo depois de mudar `data/trials.csv`.",
        "",
        "## Dados",
        "",
        f"- Trials analisados: **{len(df)}** ({por_tratamento.get('com_ia', 0)} com IA, "
        f"{por_tratamento.get('sem_ia', 0)} sem IA), de **{n_integrantes}** integrantes.",
        f"- Trials censurados no time-box (tempo registrado como 35 min): **{n_censurados}**.",
        "- Pareamento: mediana de cada integrante em cada tratamento. Cada integrante resolve "
        "cada kata uma única vez, então o par é o integrante, não a kata.",
        f"- Teste: Wilcoxon signed-rank pareado, bilateral, alpha = {ALPHA}. O p unilateral, "
        "na direção da H1, aparece como complemento.",
        "",
        "## Estatística descritiva por tratamento",
        "",
        tabela_markdown(desc, ["metrica", "tratamento", "n", "mediana", "q1", "q3", "iqr", "minimo", "maximo"]),
        "",
        "Trials com todos os testes passando: "
        + ", ".join(f"{t} = {fmt(v, 1)}%" for t, v in sucesso_total.items())
        + ".",
        "",
        "## Outliers (cercas de Tukey, 1,5 × IQR, por tratamento)",
        "",
    ]
    if outliers.empty:
        linhas.append("Nenhum trial fora das cercas.")
    else:
        linhas += [
            "Outliers são apenas sinalizados e **permanecem** na análise. O teste usa postos e a "
            "mediana por integrante, que são pouco sensíveis a valores extremos.",
            "",
            tabela_markdown(outliers, ["metrica", "tratamento", "integrante", "kata", "valor", "cerca_inferior", "cerca_superior"]),
        ]

    linhas += [
        "",
        "## Wilcoxon pareado (com_ia − sem_ia)",
        "",
        tabela_markdown(testes, [
            "metrica", "n_pares", "n_pares_nao_nulos", "mediana_com_ia", "mediana_sem_ia",
            "mediana_diferenca", "W", "p_bilateral", "p_unilateral", "rank_biserial", "rejeita_h0",
        ], casas=4),
        "",
        "`rank_biserial` vai de −1 a 1. Valor negativo indica valores menores com IA. "
        "Como referência, |r| ≥ 0,1 é um efeito pequeno, ≥ 0,3 é médio e ≥ 0,5 é grande.",
        "",
    ]
    for _, t in testes.iterrows():
        if t["observacao"]:
            linhas.append(f"- **{t['metrica']}**: {t['observacao']}.")

    tempo = testes.set_index("metrica").loc["tempo_ate_verde_min"]
    falhando = testes.set_index("metrica").loc["testes_falhando"]
    linhas += [
        "",
        "## Conclusão",
        "",
        "- **RQ1:** " + conclusao(tempo, "o tempo até passar em todos os testes"),
        "- **RQ2:** " + conclusao(falhando, "o número de testes falhando"),
        "",
    ]
    return "\n".join(linhas)


def conclusao(teste: pd.Series, descricao: str) -> str:
    if teste["n_pares_nao_nulos"] == 0:
        return (f"não houve diferença entre os tratamentos para {descricao} (todas as diferenças "
                "pareadas são zero). H0 não é rejeitada.")
    direcao = "menor" if teste["mediana_diferenca"] < 0 else "maior"
    if teste["rejeita_h0"]:
        return (f"H0 rejeitada (p = {fmt(teste['p_bilateral'], 4)}). Com IA, {descricao} foi {direcao}: "
                f"a diferença mediana pareada é {fmt(teste['mediana_diferenca'])} e r = "
                f"{fmt(teste['rank_biserial'])}.")
    return (f"H0 não rejeitada (p = {fmt(teste['p_bilateral'], 4)}). A diferença mediana pareada "
            f"é {fmt(teste['mediana_diferenca'])} ({direcao} com IA) e r = {fmt(teste['rank_biserial'])}.")


def main() -> None:
    df = carrega_trials()
    metricas = list(METRICAS)

    desc = descritiva(df, metricas)
    outliers = outliers_iqr(df, metricas)
    pares = pares_por_integrante(df, metricas)
    testes = pd.DataFrame([wilcoxon_pareado(pares, m, h1) for m, h1 in METRICAS.items()])

    SAIDA_DIR.mkdir(parents=True, exist_ok=True)
    colunas_trial = ["trial_id", "integrante", "kata", "tratamento", "status", "censurado",
                     "tempo_ate_verde_min", "testes_passando", "testes_total", "testes_falhando", "taxa_sucesso"]
    df[colunas_trial].to_csv(SAIDA_DIR / "rq1_rq2_trials.csv", index=False)
    desc.to_csv(SAIDA_DIR / "rq1_rq2_descritiva.csv", index=False)
    outliers.to_csv(SAIDA_DIR / "rq1_rq2_outliers.csv", index=False)
    pares.to_csv(SAIDA_DIR / "rq1_rq2_pares.csv", index=False)
    testes.to_csv(SAIDA_DIR / "rq1_rq2_wilcoxon.csv", index=False)

    RELATORIO_MD.write_text(gera_relatorio(df, desc, outliers, testes), encoding="utf-8")

    print(testes[["metrica", "n_pares", "mediana_com_ia", "mediana_sem_ia", "p_bilateral", "rank_biserial"]].to_string(index=False))
    print(f"\nSaidas em {SAIDA_DIR.relative_to(BASE_DIR)} e {RELATORIO_MD.relative_to(BASE_DIR)}")


if __name__ == "__main__":
    main()
