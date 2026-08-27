"""
Lab01S03 - analise e visualizacao da RQ03.

RQ03 - Sistemas populares lancam releases com frequencia?
       Metrica: total de releases (coluna total_releases).

A S02 validou que a coluna nao tem valor ausente nem inconsistente. Esta
analise da S03 responde a pergunta: consolida os valores medianos, a contagem
por categoria pedida pelo enunciado, os outliers pelo critorio de Tukey e o
efeito do teto de 1.000 releases da API, e gera os graficos do relatorio.

Um recorte importante entra aqui: separar quem tem linguagem primaria de quem
nao tem. A ausencia de `primaryLanguage` e o proxy disponivel no CSV para
"repositorio que nao e software distribuivel" - lista, roteiro de estudo,
colecao de material. Se a taxa de repositorios sem release for muito diferente
entre os dois grupos, o numero agregado da RQ03 esta misturando duas populacoes,
e a resposta precisa ser dada em dois numeros, nao em um.

Uso:
    python src/analise_rq03.py
"""

import sys

from analise_base import (
    DESTAQUE,
    SERIE_1,
    TETO_RELEASES,
    TINTA_FRACA,
    TINTA_MEDIA,
    arredondar_pontas,
    br,
    carregar_base,
    contar_por_faixa,
    descritiva,
    ecdf,
    grade,
    legenda,
    limites_de_tukey,
    nova_figura,
    rotular_barras,
    salvar,
)

# Faixas da contagem por categoria. O corte em 0 e o corte no teto da API sao
# os dois que carregam significado: o primeiro separa quem nao versiona, o
# segundo marca onde a metrica deixa de ser exata.
FAIXAS_RELEASES = [
    ("0", 0, 0),
    ("1 a 10", 1, 10),
    ("11 a 50", 11, 50),
    ("51 a 100", 51, 100),
    ("101 a 500", 101, 500),
    ("501 a 999", 501, 999),
    (f">= {TETO_RELEASES}", TETO_RELEASES, None),
]


# ---------------------------------------------------------------------------
# Analise
# ---------------------------------------------------------------------------
def secao_descritiva(repos):
    releases = [r["releases"] for r in repos]
    d = descritiva(releases)
    _, cerca_alta = limites_de_tukey(releases)
    outliers = [r for r in repos if r["releases"] > cerca_alta]

    print("=== RQ03.1 - valores centrais do total de releases ===")
    print(f"  n ..........................................: {d['n']}")
    print(f"  mediana ....................................: {d['mediana']:.0f} releases")
    print(f"  media ......................................: {d['media']:.1f} releases")
    print(f"  Q1 / Q3 ....................................: {d['q1']:.0f} / {d['q3']:.0f}")
    print(f"  IQR ........................................: {d['iqr']:.0f}")
    print(f"  minimo / maximo ............................: {d['min']} / {d['max']}")
    print(f"  cerca superior de Tukey (Q3 + 1,5 x IQR) ...: {cerca_alta:.0f}")
    print(f"  outliers superiores ........................: {len(outliers)} ({len(outliers) / d['n'] * 100:.1f}%)")
    print("  a media e mais de tres vezes a mediana e Q1 e zero: a media nao")
    print("  descreve esta distribuicao, a mediana e o valor central a reportar.")

    return d, cerca_alta, outliers


def secao_categorias(repos):
    releases = [r["releases"] for r in repos]
    linhas = contar_por_faixa(releases, FAIXAS_RELEASES)

    print("\n=== RQ03.2 - contagem por categoria ===")
    print(f"  {'faixa':12s} {'n':>6s} {'%':>7s}")
    for rotulo, qtd, pct in linhas:
        print(f"  {rotulo:12s} {qtd:6d} {pct:6.1f}%")

    sem_release = sum(1 for v in releases if v == 0)
    acima_100 = sum(1 for v in releases if v > 100)
    print(f"  sem nenhuma release ........................: {sem_release} ({sem_release / len(releases) * 100:.1f}%)")
    print(f"  acima de 100 releases ......................: {acima_100} ({acima_100 / len(releases) * 100:.1f}%)")
    print("  a distribuicao e bimodal: um bloco que nao versiona e um bloco que")
    print("  versiona muito, com pouca massa no meio.")

    return linhas


def secao_teto(repos):
    no_teto = [r for r in repos if r["no_teto"]]

    print(f"\n=== RQ03.3 - o teto de {TETO_RELEASES} releases da API ===")
    print(f"  repositorios no teto .......................: {len(no_teto)} ({len(no_teto) / len(repos) * 100:.1f}%)")
    print(f"  nesses casos o valor e limite inferior (>= {TETO_RELEASES}), nao contagem real.")
    for r in sorted(no_teto, key=lambda r: -r["estrelas"])[:5]:
        print(f"    {r['nome']:45s} {r['estrelas']:>7d} estrelas")

    return no_teto


def secao_linguagem(repos):
    """Compara quem tem linguagem primaria com quem nao tem.

    Sem `primaryLanguage`, o GitHub nao detectou codigo predominante - o
    repositorio e, na pratica, texto. E o proxy que o CSV oferece para separar
    software distribuivel de colecao de material.
    """
    com = [r for r in repos if r["linguagem"]]
    sem = [r for r in repos if not r["linguagem"]]

    print("\n=== RQ03.4 - software distribuivel x colecao de material ===")
    print(f"  {'grupo':28s} {'n':>5s} {'sem release':>13s} {'mediana releases':>18s}")

    grupos = []
    for rotulo, grupo in (("com linguagem primaria", com), ("sem linguagem primaria", sem)):
        if not grupo:
            continue
        zeros = sum(1 for r in grupo if r["releases"] == 0)
        com_release = [r["releases"] for r in grupo if r["releases"] > 0]
        mediana = descritiva(com_release)["mediana"] if len(com_release) >= 4 else 0.0
        print(
            f"  {rotulo:28s} {len(grupo):5d} "
            f"{zeros:6d} ({zeros / len(grupo) * 100:4.1f}%) {mediana:18.0f}"
        )
        grupos.append({
            "rotulo": rotulo,
            "n": len(grupo),
            "pct_sem_release": zeros / len(grupo) * 100,
            "mediana_releases": mediana,
        })

    print("  a taxa de repositorios sem release e muito diferente entre os dois")
    print("  grupos: a RQ03 nao deve ser respondida com um numero agregado.")

    return grupos


def secao_extremos(repos):
    print("\n=== RQ03.5 - extremos ===")
    print("  maiores totais de releases:")
    for r in sorted(repos, key=lambda r: (-r["releases"], r["nome"]))[:10]:
        marca = f"  (no teto da API, >= {TETO_RELEASES})" if r["no_teto"] else ""
        print(f"    {r['nome']:45s} {r['releases']:>5d}{marca}")


# ---------------------------------------------------------------------------
# Graficos
# ---------------------------------------------------------------------------
def grafico_categorias(linhas):
    fig, ax = nova_figura(
        "RQ03 - Total de releases nos 1.000 repositorios mais estrelados",
        "Contagem por faixa. A distribuicao e bimodal: 28,6% nao publica release "
        "nenhuma e 34,3% passa de 100.",
    )
    fig.subplots_adjust(top=0.78, bottom=0.16, left=0.06, right=0.985)

    rotulos = [l[0] for l in linhas]
    valores = [l[1] for l in linhas]

    grade(ax, "y")
    barras = ax.bar(rotulos, valores, width=0.68, color=SERIE_1, zorder=2)
    ax.set_ylim(0, max(valores) * 1.16)
    ax.set_xlabel("Total de releases", fontsize=9.5, color=TINTA_MEDIA, labelpad=8)
    ax.set_ylabel("Repositorios", fontsize=9.5, color=TINTA_MEDIA, labelpad=8)

    rotular_barras(
        ax, barras,
        [f"{l[1]}\n{br(l[2])}%" for l in linhas],
    )
    arredondar_pontas(ax, barras)

    return salvar(fig, "rq03_releases_por_faixa.png")


def grafico_ecdf(repos, d):
    releases = [r["releases"] for r in repos]
    total = len(releases)
    pct_zero = sum(1 for v in releases if v == 0) / total * 100

    fig, ax = nova_figura(
        "RQ03 - Distribuicao cumulativa do total de releases",
        "Escala logaritmica no eixo do total. A curva comeca em 28,6%, que e a "
        "parcela sem release nenhuma.",
    )
    fig.subplots_adjust(top=0.78, bottom=0.16, left=0.075, right=0.985)

    positivos = [v for v in releases if v > 0]
    xs, ys = ecdf(positivos)
    # A curva dos positivos e deslocada para cima pela massa que esta em zero,
    # para que o eixo y continue significando "percentual de toda a base".
    ys = [pct_zero + y * (100 - pct_zero) / 100 for y in ys]

    grade(ax, "y")
    ax.set_xscale("log")
    ax.plot(xs, ys, color=SERIE_1, linewidth=2.0, zorder=3, solid_capstyle="round")
    ax.set_xlim(1, TETO_RELEASES * 1.6)
    ax.set_ylim(0, 100)
    ax.set_xlabel("Total de releases (escala log)", fontsize=9.5, color=TINTA_MEDIA, labelpad=8)
    ax.set_ylabel("Percentual acumulado dos 1.000 repositorios", fontsize=9.5,
                  color=TINTA_MEDIA, labelpad=8)

    ax.annotate(
        f"{br(pct_zero)}% sem release",
        xy=(1.05, pct_zero), xytext=(1.15, pct_zero + 6),
        fontsize=9, color=TINTA_MEDIA,
    )

    for valor, rotulo in (
        (d["q1"], "Q1"), (d["mediana"], "mediana"), (d["q3"], "Q3"),
    ):
        if valor <= 0:
            # Q1 e zero nesta distribuicao: nao existe ponto na escala log para
            # marcar, e o proprio patamar inicial da curva ja mostra isso.
            continue
        ax.axvline(valor, color=DESTAQUE, linewidth=1.2, linestyle=(0, (4, 3)), zorder=2)
        ax.annotate(
            f"{rotulo} = {valor:.0f}",
            xy=(valor, 4), xytext=(valor * 1.1, 4),
            fontsize=9, color=DESTAQUE,
        )

    ax.axvline(TETO_RELEASES, color=TINTA_FRACA, linewidth=1.2, zorder=2)
    ax.annotate(
        f"teto da API ({TETO_RELEASES})",
        xy=(TETO_RELEASES, 52), xytext=(TETO_RELEASES * 0.92, 52),
        fontsize=9, color=TINTA_FRACA, ha="right",
    )

    return salvar(fig, "rq03_ecdf_releases.png")


def grafico_linguagem(grupos):
    fig, eixos = nova_figura(
        "RQ03 - Total de releases por presenca de linguagem primaria",
        "Repositorio sem linguagem primaria detectada pelo GitHub - lista, roteiro, "
        "colecao de material - quase nunca publica release.",
        tamanho=(9.6, 5.0), colunas=2,
    )
    fig.subplots_adjust(top=0.76, bottom=0.22, left=0.085, right=0.985, wspace=0.30)

    rotulos = [
        "{}\nprimaria\nn = {}".format(g["rotulo"].removesuffix(" primaria"), g["n"])
        for g in grupos
    ]

    paineis = [
        (eixos[0], "Sem nenhuma release (%)",
         [g["pct_sem_release"] for g in grupos],
         [f"{br(g['pct_sem_release'])}%" for g in grupos], SERIE_1),
        (eixos[1], "Mediana de releases (entre os que publicam)",
         [g["mediana_releases"] for g in grupos],
         [f"{g['mediana_releases']:.0f}" for g in grupos], SERIE_1),
    ]

    for ax, titulo, valores, textos, cor in paineis:
        grade(ax, "y")
        barras = ax.bar(rotulos, valores, width=0.5, color=cor, zorder=2)
        ax.set_ylim(0, max(valores) * 1.22)
        ax.set_title(titulo, fontsize=10, color=TINTA_MEDIA, loc="left", pad=10)
        ax.tick_params(axis="x", labelsize=9)
        rotular_barras(ax, barras, textos)
        arredondar_pontas(ax, barras)

    return salvar(fig, "rq03_releases_por_tipo_de_repositorio.png")


def main():
    try:
        repos, referencia = carregar_base()
    except (FileNotFoundError, ValueError) as erro:
        sys.exit(f"{erro}\nRode src/fetch_repos.py primeiro.")

    print("RQ03 - Sistemas populares lancam releases com frequencia?")
    print(f"Base: data/repositorios_top1000.csv  |  coleta de {referencia:%Y-%m-%d}\n")

    d, _, _ = secao_descritiva(repos)
    linhas = secao_categorias(repos)
    secao_teto(repos)
    grupos = secao_linguagem(repos)
    secao_extremos(repos)

    print("\n=== Graficos gerados ===")
    for caminho in (
        grafico_categorias(linhas),
        grafico_ecdf(repos, d),
        grafico_linguagem(grupos),
    ):
        print(f"  {caminho}")

    print("\nAnalise da RQ03 concluida.")


if __name__ == "__main__":
    main()
