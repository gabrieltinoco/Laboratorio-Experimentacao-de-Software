"""Gera o dashboard visual do Lab02S03 (Integrante C).

Os graficos usam os CSVs derivados pelas analises de RQ1/RQ2 e RQ3. Para
reproduzir o painel, execute a partir da pasta Laboratorio02:

    python src/dashboard.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


BASE_DIR = Path(__file__).resolve().parent.parent
ANALISE_DIR = BASE_DIR / "data" / "analise"
GRAFICOS_DIR = BASE_DIR / "graficos"
TRATAMENTOS = ["com_ia", "sem_ia"]
CORES = {"com_ia": "#0f766e", "sem_ia": "#d97706"}
ROTULOS = {"com_ia": "Com IA", "sem_ia": "Sem IA"}


def carrega_dados() -> tuple[pd.DataFrame, pd.DataFrame]:
    rqs12 = pd.read_csv(ANALISE_DIR / "rq1_rq2_trials.csv")
    rq3 = pd.read_csv(BASE_DIR / "data" / "metricas.csv")
    numericas_rq12 = ["tempo_ate_verde_min", "testes_passando", "testes_total", "testes_falhando", "taxa_sucesso"]
    numericas_rq3 = ["cc_media", "dup_percentual", "sloc", "mi_medio"]
    for coluna in numericas_rq12:
        rqs12[coluna] = pd.to_numeric(rqs12[coluna], errors="coerce")
    for coluna in numericas_rq3:
        rq3[coluna] = pd.to_numeric(rq3[coluna], errors="coerce")
    return rqs12, rq3


def prepara_radar(rqs12: pd.DataFrame, rq3: pd.DataFrame) -> pd.DataFrame:
    """Calcula medianas normalizadas, onde valores maiores indicam melhor perfil."""
    valores = pd.DataFrame(
        {
            "Tempo (menor e melhor)": rqs12.groupby("tratamento")["tempo_ate_verde_min"].median(),
            "Taxa de sucesso": rqs12.groupby("tratamento")["taxa_sucesso"].median(),
            "Complexidade CC (menor e melhor)": rq3.groupby("tratamento")["cc_media"].median(),
            "Duplicacao (menor e melhor)": rq3.groupby("tratamento")["dup_percentual"].median(),
            "SLOC (menor e melhor)": rq3.groupby("tratamento")["sloc"].median(),
        }
    ).reindex(TRATAMENTOS)

    normalizado = pd.DataFrame(index=valores.index)
    for coluna in valores.columns:
        serie = valores[coluna]
        minimo, maximo = serie.min(), serie.max()
        if pd.isna(minimo) or pd.isna(maximo):
            normalizado[coluna] = np.nan
        elif minimo == maximo:
            normalizado[coluna] = 1.0
        else:
            escala = (serie - minimo) / (maximo - minimo)
            normalizado[coluna] = 1 - escala if "menor" in coluna else escala
    normalizado.index.name = "tratamento"
    return normalizado.reset_index()


def marca_censura(ax: plt.Axes, dados: pd.DataFrame) -> None:
    censurados = dados[dados["censurado"]].groupby("tratamento").size()
    texto = ", ".join(f"{ROTULOS[t]}: {int(c)}" for t, c in censurados.items())
    ax.axhline(35, color="#b91c1c", linestyle="--", linewidth=1.3, label="Time-box: 35 min")
    ax.text(0.98, 0.97, f"Censurados: {texto or 'nenhum'}", transform=ax.transAxes,
            ha="right", va="top", fontsize=8, color="#7f1d1d")


def desenha_dashboard(rqs12: pd.DataFrame, rq3: pd.DataFrame, destino: Path) -> None:
    sns.set_theme(style="whitegrid", context="notebook")
    fig, axes = plt.subplots(2, 2, figsize=(15, 10), constrained_layout=True)
    fig.suptitle("Lab02 | Assistente de IA versus codificacao manual", fontsize=18, fontweight="bold")

    ax = axes[0, 0]
    sns.boxplot(data=rqs12, x="tratamento", y="tempo_ate_verde_min", order=TRATAMENTOS,
                hue="tratamento", palette=CORES, legend=False, width=0.55, ax=ax)
    sns.stripplot(data=rqs12, x="tratamento", y="tempo_ate_verde_min", order=TRATAMENTOS,
                  color="#1f2937", alpha=0.55, jitter=0.13, size=4, ax=ax)
    marca_censura(ax, rqs12)
    ax.set(title="RQ1 | Tempo ate o verde", xlabel="", ylabel="Minutos")
    ax.set_xticks(range(len(TRATAMENTOS)), [ROTULOS[t] for t in TRATAMENTOS])
    ax.legend(loc="upper left", fontsize=8)

    ax = axes[0, 1]
    sucesso = rqs12.groupby(["kata", "tratamento"], as_index=False)["testes_passando"].median()
    sns.barplot(data=sucesso, x="kata", y="testes_passando", hue="tratamento", order=sorted(sucesso["kata"].unique()),
                hue_order=TRATAMENTOS, palette=CORES, ax=ax)
    ax.set(title="RQ2 | Testes passando por kata", xlabel="Kata", ylabel="Mediana de testes (de 8)")
    ax.set_ylim(0, 8.8)
    ax.tick_params(axis="x", rotation=25)
    ax.legend(title="Tratamento", labels=[ROTULOS[t] for t in TRATAMENTOS])

    ax = axes[1, 0]
    sns.scatterplot(data=rq3, x="sloc", y="cc_media", hue="tratamento", style="tratamento",
                    hue_order=TRATAMENTOS, palette=CORES, s=90, ax=ax)
    ax.set(title="RQ3 | SLOC versus complexidade ciclomática", xlabel="SLOC (controle)", ylabel="CC media (Radon)")
    ax.legend(title="Tratamento", labels=[ROTULOS[t] for t in TRATAMENTOS])

    ax = axes[1, 1]
    estrutural = rq3.melt(id_vars="tratamento", value_vars=["dup_percentual", "mi_medio"],
                          var_name="metrica", value_name="valor")
    estrutural["metrica"] = estrutural["metrica"].map({"dup_percentual": "Duplicacao (%)", "mi_medio": "MI"})
    sns.boxplot(data=estrutural, x="metrica", y="valor", hue="tratamento", hue_order=TRATAMENTOS,
                palette=CORES, ax=ax)
    ax.set(title="RQ3 | Duplicacao e manutenibilidade", xlabel="", ylabel="Valor")
    ax.legend(title="Tratamento", labels=[ROTULOS[t] for t in TRATAMENTOS])

    destino.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destino, dpi=180, bbox_inches="tight")
    plt.close(fig)


def desenha_radar(radar: pd.DataFrame, destino: Path) -> None:
    categorias = [coluna for coluna in radar.columns if coluna != "tratamento"]
    angulos = np.linspace(0, 2 * np.pi, len(categorias), endpoint=False).tolist()
    angulos += angulos[:1]
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={"polar": True})
    for _, linha in radar.iterrows():
        valores = linha[categorias].tolist()
        valores += valores[:1]
        ax.plot(angulos, valores, linewidth=2, color=CORES[linha["tratamento"]], label=ROTULOS[linha["tratamento"]])
        ax.fill(angulos, valores, color=CORES[linha["tratamento"]], alpha=0.12)
    ax.set_xticks(angulos[:-1])
    ax.set_xticklabels(categorias, fontsize=9)
    ax.set_ylim(0, 1)
    ax.set_title("Visao geral | Medianas normalizadas (maior = melhor)", pad=25, fontweight="bold")
    ax.legend(loc="upper right", bbox_to_anchor=(1.22, 1.12))
    destino.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destino, dpi=180, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sem-exibir", action="store_true", help="Mantido para compatibilidade; o script sempre salva os arquivos.")
    args = parser.parse_args()
    del args
    rqs12, rq3 = carrega_dados()
    radar = prepara_radar(rqs12, rq3)
    radar.to_csv(ANALISE_DIR / "dashboard_radar.csv", index=False)
    desenha_dashboard(rqs12, rq3, GRAFICOS_DIR / "dashboard_lab02.png")
    desenha_radar(radar, GRAFICOS_DIR / "dashboard_radar.png")
    print("Dashboard salvo em graficos/dashboard_lab02.png e graficos/dashboard_radar.png")


if __name__ == "__main__":
    main()