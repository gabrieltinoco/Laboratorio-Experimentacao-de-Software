"""
Analise estatistica da RQ3 (estrutura do codigo) - Lab02S03, Integrante B.

Le data/metricas.csv, produzido por src/metricas_estaticas.py (Radon + jscpd),
e compara os tratamentos em complexidade ciclomatica, duplicacao e LOC. Gera:

    data/analise/rq3_descritiva.csv  mediana, quartis e IQR por tratamento
    data/analise/rq3_outliers.csv    trials fora das cercas de Tukey
    data/analise/rq3_pares.csv       mediana por integrante em cada tratamento
    data/analise/rq3_wilcoxon.csv    Wilcoxon pareado e tamanho de efeito
    docs/analise_rq3.md              resumo legivel dos resultados

LOC (sloc) e sempre reportado junto de complexidade e duplicacao, como exige o
enunciado: codigo mais longo tende a somar mais complexidade sem ser, por
funcao, mais complexo.

Uso:
    python src/analise_rq3.py            # usa data/metricas.csv como esta
    python src/analise_rq3.py --coletar  # roda antes metricas_estaticas.py --todos
"""

from __future__ import annotations

import argparse
import subprocess
import sys
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
METRICAS_CSV = BASE_DIR / "data" / "metricas.csv"
TRIALS_CSV = BASE_DIR / "data" / "trials.csv"
SAIDA_DIR = BASE_DIR / "data" / "analise"
RELATORIO_MD = BASE_DIR / "docs" / "analise_rq3.md"

# A H1 da RQ3 e bilateral ("altera"), entao todas as metricas usam two-sided.
METRICAS = ["cc_media", "cc_total_por_kloc", "dup_percentual", "sloc", "mi_medio"]
DESCRICAO = {
    "cc_media": "complexidade ciclomática média por função",
    "cc_total_por_kloc": "complexidade total por KLOC",
    "dup_percentual": "% de linhas duplicadas",
    "sloc": "SLOC (controle)",
    "mi_medio": "Índice de Manutenibilidade (opcional)",
}


def coleta_metricas() -> None:
    """Atualiza data/metricas.csv com todos os trials que tem codigo em trials/."""
    subprocess.run([sys.executable, str(BASE_DIR / "src" / "metricas_estaticas.py"), "--todos"], check=True)


def carrega_metricas() -> pd.DataFrame:
    df = pd.read_csv(METRICAS_CSV, dtype={"trial_id": str, "integrante": str})
    for coluna in METRICAS:
        df[coluna] = pd.to_numeric(df[coluna], errors="coerce")
    return df


def gera_relatorio(df: pd.DataFrame, n_trials_total: int, desc: pd.DataFrame,
                   outliers: pd.DataFrame, pares: pd.DataFrame, testes: pd.DataFrame) -> str:
    por_tratamento = df.groupby("tratamento").size().to_dict()
    sem_codigo = n_trials_total - len(df)

    linhas = [
        "# Análise RQ3 (estrutura do código)",
        "",
        "> Arquivo gerado por [`src/analise_rq3.py`](../src/analise_rq3.py). "
        "Não editar à mão: rode `python src/analise_rq3.py --coletar` depois de adicionar código em `trials/`.",
        "",
        "## Dados",
        "",
        f"- Trials com métricas estáticas: **{len(df)}** ({por_tratamento.get('com_ia', 0)} com IA, "
        f"{por_tratamento.get('sem_ia', 0)} sem IA), de **{df['integrante'].nunique()}** integrantes "
        f"({len(pares)} pares completos).",
        f"- Trials registrados em `data/trials.csv` sem pasta de código em `trials/`: **{sem_codigo}**. "
        "Eles entram na RQ1/RQ2, mas não podem ser medidos na RQ3.",
        "- Ferramentas: Radon (complexidade, LOC, MI) e jscpd (duplicação), com os testes de aceitação "
        "excluídos da medição (ver [`docs/metricas_estaticas.md`](metricas_estaticas.md)).",
        f"- Teste: Wilcoxon signed-rank pareado por integrante, bilateral, alpha = {ALPHA}.",
        "",
        "## Métricas usadas",
        "",
        *[f"- `{m}`: {DESCRICAO[m]}." for m in METRICAS],
        "",
        "## Estatística descritiva por tratamento",
        "",
        tabela_markdown(desc, ["metrica", "tratamento", "n", "mediana", "q1", "q3", "iqr", "minimo", "maximo"]),
        "",
        "## Outliers (cercas de Tukey, 1,5 × IQR, por tratamento)",
        "",
        "Nenhum trial fora das cercas." if outliers.empty else
        tabela_markdown(outliers, ["metrica", "tratamento", "integrante", "kata", "valor", "cerca_inferior", "cerca_superior"]),
        "",
        "## Wilcoxon pareado (com_ia − sem_ia)",
        "",
        tabela_markdown(testes, [
            "metrica", "n_pares", "n_pares_nao_nulos", "mediana_com_ia", "mediana_sem_ia",
            "mediana_diferenca", "W", "p_bilateral", "rank_biserial", "rejeita_h0",
        ], casas=4),
        "",
    ]
    for _, t in testes.iterrows():
        if t["observacao"]:
            linhas.append(f"- **{t['metrica']}**: {t['observacao']}.")

    rejeitadas = testes[testes["rejeita_h0"]]["metrica"].tolist()
    linhas += ["", "## Conclusão", ""]
    if rejeitadas:
        linhas.append(
            "- **RQ3:** H0 rejeitada para " + ", ".join(f"`{m}`" for m in rejeitadas)
            + ". O uso de IA alterou a estrutura do código nessas métricas. Leia sempre junto de `sloc`."
        )
    else:
        linhas.append(
            "- **RQ3:** H0 não rejeitada para nenhuma métrica. Com os dados disponíveis, não há evidência "
            "de que o uso de IA altere complexidade, duplicação ou LOC."
        )
    if len(pares) < 6:
        linhas.append(
            f"- Com {len(pares)} pares, o Wilcoxon não tem como atingir p < {ALPHA}. O resultado da RQ3 "
            "deve ser lido como descritivo até que o código dos demais trials seja commitado em `trials/`."
        )
    linhas.append("")
    return "\n".join(linhas)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--coletar", action="store_true", help="Roda metricas_estaticas.py --todos antes da analise")
    args = parser.parse_args()

    if args.coletar:
        coleta_metricas()
    if not METRICAS_CSV.exists():
        parser.error(f"{METRICAS_CSV.relative_to(BASE_DIR)} nao existe; rode com --coletar")

    df = carrega_metricas()
    n_trials_total = len(pd.read_csv(TRIALS_CSV)) if TRIALS_CSV.exists() else len(df)

    desc = descritiva(df, METRICAS)
    outliers = outliers_iqr(df, METRICAS)
    pares = pares_por_integrante(df, METRICAS)
    pares = pares.dropna(subset=[f"{METRICAS[0]}_com_ia", f"{METRICAS[0]}_sem_ia"])
    testes = pd.DataFrame([wilcoxon_pareado(pares, m, "two-sided") for m in METRICAS])

    SAIDA_DIR.mkdir(parents=True, exist_ok=True)
    desc.to_csv(SAIDA_DIR / "rq3_descritiva.csv", index=False)
    outliers.to_csv(SAIDA_DIR / "rq3_outliers.csv", index=False)
    pares.to_csv(SAIDA_DIR / "rq3_pares.csv", index=False)
    testes.to_csv(SAIDA_DIR / "rq3_wilcoxon.csv", index=False)

    RELATORIO_MD.write_text(gera_relatorio(df, n_trials_total, desc, outliers, pares, testes), encoding="utf-8")

    print(testes[["metrica", "n_pares", "mediana_com_ia", "mediana_sem_ia", "p_bilateral", "observacao"]].to_string(index=False))
    print(f"\nSaidas em {SAIDA_DIR.relative_to(BASE_DIR)} e {RELATORIO_MD.relative_to(BASE_DIR)}")


if __name__ == "__main__":
    main()
