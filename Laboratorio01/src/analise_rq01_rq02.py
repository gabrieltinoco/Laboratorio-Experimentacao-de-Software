"""Lab01S03 - analise e visualizacao das RQs 01 e 02.

Gera estatisticas reproduziveis e figuras a partir do CSV dos 1.000
repositorios, usando a data de referencia reconstruida pela base comum.

Uso:
    python src/analise_rq01_rq02.py
"""

import csv
import statistics

from analise_base import (
    DESTAQUE,
    SERIE_1,
    TINTA_MEDIA,
    arredondar_pontas,
    br,
    carregar_base,
    contar_por_faixa,
    grade,
    nova_figura,
    salvar,
)


FAIXAS_IDADE = [
    ("< 5 anos", 0, 5),
    ("5 a 10 anos", 5, 10),
    (">= 10 anos", 10, None),
]

FAIXAS_PRS = [
    ("0", 0, 0),
    ("1 a 499", 1, 499),
    ("500 a 4.999", 500, 4999),
    (">= 5.000", 5000, None),
]


def analisar(repos):
    idades = [r["idade"] for r in repos]
    prs = [r["prs"] for r in repos]
    resultados = []
    for rotulo, valores, faixas in (
        ("RQ01", idades, FAIXAS_IDADE),
        ("RQ02", prs, FAIXAS_PRS),
    ):
        q1, _, q3 = statistics.quantiles(valores, n=4, method="inclusive")
        d = {
            "n": len(valores),
            "mediana": statistics.median(valores),
            "media": statistics.mean(valores),
            "q1": q1,
            "q3": q3,
            "iqr": q3 - q1,
            "min": min(valores),
            "max": max(valores),
        }
        limite_inferior = q1 - 1.5 * d["iqr"]
        limite_superior = q3 + 1.5 * d["iqr"]
        chave = "idade" if rotulo == "RQ01" else "prs"
        outliers = [r for r in repos if r[chave] < limite_inferior or r[chave] > limite_superior]
        resultados.append((rotulo, d, limite_inferior, limite_superior, outliers, contar_por_faixa(valores, faixas)))
    return resultados


def imprimir_resultados(repos, resultados, referencia):
    print(f"Data de referencia: {referencia.isoformat()}")
    for rotulo, d, limite_inferior, limite_superior, outliers, faixas in resultados:
        print(f"\n=== {rotulo} ===")
        print(f"  n: {d['n']}")
        print(f"  mediana: {d['mediana']:.2f}")
        print(f"  media: {d['media']:.2f}")
        print(f"  Q1 / Q3: {d['q1']:.2f} / {d['q3']:.2f}")
        print(f"  IQR: {d['iqr']:.2f}")
        print(f"  minimo / maximo: {d['min']:.2f} / {d['max']:.2f}")
        print(f"  cercas de Tukey: < {limite_inferior:.2f} ou > {limite_superior:.2f}")
        print(f"  outliers: {len(outliers)} ({len(outliers) / d['n'] * 100:.1f}%)")
        print("  faixas:")
        for faixa, quantidade, percentual in faixas:
            print(f"    {faixa:15s} {quantidade:4d} ({percentual:5.1f}%)")
        if outliers:
            valor = "idade" if rotulo == "RQ01" else "prs"
            print("  maiores extremos:")
            for repositorio in sorted(outliers, key=lambda r: -r[valor])[:5]:
                print(f"    {repositorio['nome']:45s} {repositorio[valor]:.2f}")


def grafico_faixas(resultados):
    for rotulo, _, _, _, _, faixas in resultados:
        titulo = "RQ01 - Idade dos repositorios mais estrelados" if rotulo == "RQ01" else "RQ02 - PRs aceitas nos repositorios mais estrelados"
        eixo = "Idade do repositorio" if rotulo == "RQ01" else "Pull requests aceitas"
        nome = "rq01_idade_por_faixa.png" if rotulo == "RQ01" else "rq02_prs_por_faixa.png"
        fig, ax = nova_figura(titulo, "Contagem de repositorios por faixa; n = 1.000.")
        fig.subplots_adjust(top=0.78, bottom=0.18, left=0.08, right=0.98)
        barras = ax.bar([linha[0] for linha in faixas], [linha[1] for linha in faixas], color=SERIE_1, width=0.65, zorder=2)
        grade(ax, "y")
        ax.set_xlabel(eixo, fontsize=9.5, color=TINTA_MEDIA, labelpad=8)
        ax.set_ylabel("Repositorios", fontsize=9.5, color=TINTA_MEDIA, labelpad=8)
        ax.set_ylim(0, max(linha[1] for linha in faixas) * 1.18)
        for barra, linha in zip(barras, faixas):
            ax.text(barra.get_x() + barra.get_width() / 2, barra.get_height() + 8, f"{linha[1]}\n{br(linha[2])}%", ha="center", va="bottom", fontsize=9, color=TINTA_MEDIA)
        arredondar_pontas(ax, barras)
        salvar(fig, nome)


def grafico_distribuicao(repos):
    idades = [r["idade"] for r in repos]
    prs = [r["prs"] for r in repos]
    fig, eixos = nova_figura(
        "RQ01 e RQ02 - Distribuicoes das metricas",
        "Boxplots mostram a mediana e a dispersao; a RQ02 usa escala logaritmica para preservar a cauda longa.",
        tamanho=(9.8, 5.4), colunas=2,
    )
    fig.subplots_adjust(top=0.78, bottom=0.16, left=0.07, right=0.98, wspace=0.28)
    for ax, valores, titulo, eixo, logaritmica in (
        (eixos[0], idades, "RQ01 - Idade", "Anos", False),
        (eixos[1], prs, "RQ02 - PRs aceitas", "PRs (escala log)", True),
    ):
        grade(ax, "y")
        ax.boxplot(valores, orientation="vertical", patch_artist=True, tick_labels=[titulo],
                   boxprops={"facecolor": SERIE_1, "alpha": 0.82},
                   medianprops={"color": DESTAQUE, "linewidth": 2},
                   whiskerprops={"color": TINTA_MEDIA}, capprops={"color": TINTA_MEDIA},
                   flierprops={"marker": ".", "markerfacecolor": DESTAQUE, "markeredgecolor": DESTAQUE, "markersize": 3, "alpha": 0.45})
        if logaritmica:
            ax.set_yscale("symlog", linthresh=1)
        ax.set_ylabel(eixo, fontsize=9.5, color=TINTA_MEDIA, labelpad=8)
    salvar(fig, "rq01_rq02_boxplots.png")


def main():
    repos, referencia = carregar_base()
    from analise_base import CSV_PATH
    with open(CSV_PATH, newline="", encoding="utf-8") as arquivo:
        for repositorio, linha in zip(repos, csv.DictReader(arquivo)):
            repositorio["prs"] = int(linha["pull_requests_aceitas"])
    resultados = analisar(repos)
    imprimir_resultados(repos, resultados, referencia)
    grafico_faixas(resultados)
    grafico_distribuicao(repos)


if __name__ == "__main__":
    main()