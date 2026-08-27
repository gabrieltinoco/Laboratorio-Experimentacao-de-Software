"""
Lab01S03 - analise e visualizacao da RQ04.

RQ04 - Sistemas populares sao atualizados com frequencia?
       Metrica do enunciado: tempo ate a ultima atualizacao (`updatedAt`).
       Metrica efetiva adotada: tempo desde o ultimo push (`pushedAt`).

A troca de metrica nao e conveniencia, e resultado da S02, e esta analise a
demonstra em numero e em grafico. O `updatedAt` do GitHub sobe a cada estrela,
watch, fork ou edicao de descricao - qualquer evento de metadado, nao so
mudanca de codigo. Nos 1.000 repositorios mais estrelados do GitHub esse campo
fica saturado: eles recebem estrela o tempo inteiro, entao praticamente todos
marcam "atualizado hoje" e a metrica perde qualquer poder de discriminacao.
O `pushedAt` sobe somente com push de codigo, e e ele que separa repositorio
mantido de repositorio abandonado.

A analise reporta as duas colunas lado a lado justamente para que a troca fique
evidenciada, e nao assumida.

Uso:
    python src/analise_rq04.py
"""

import sys

from analise_base import (
    DESTAQUE,
    SERIE_1,
    SERIE_2,
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

# Faixas da contagem por categoria. O corte de 365 dias e o que decide a
# pergunta: acima dele o repositorio nao recebeu uma linha de codigo em um ano.
# A primeira faixa e aberta embaixo para acomodar o valor negativo gerado por
# push ocorrido durante a coleta (1 caso, documentado na S02).
FAIXAS_DIAS = [
    ("ate 7 dias", None, 7),
    ("8 a 30 dias", 8, 30),
    ("31 a 90 dias", 31, 90),
    ("91 a 365 dias", 91, 365),
    ("mais de 365 dias", 366, None),
]

CORTE_ABANDONO = 365


# ---------------------------------------------------------------------------
# Analise
# ---------------------------------------------------------------------------
def secao_comparacao(repos):
    """Mostra por que a metrica literal do enunciado nao responde a RQ04."""
    update = [r["dias_update"] for r in repos]
    push = [r["dias_push"] for r in repos]

    print("=== RQ04.1 - a metrica literal do enunciado nao discrimina ===")
    print(f"  {'coluna':34s} {'mediana':>8s} {'Q1':>6s} {'Q3':>7s} {'min':>6s} {'max':>7s}")

    for rotulo, valores in (
        ("dias desde updatedAt (enunciado)", update),
        ("dias desde pushedAt (efetiva)", push),
    ):
        d = descritiva(valores)
        print(
            f"  {rotulo:34s} {d['mediana']:8.0f} {d['q1']:6.0f} "
            f"{d['q3']:7.0f} {d['min']:6.0f} {d['max']:7.0f}"
        )

    zerados = sum(1 for v in update if v <= 0)
    print(f"  repositorios com updatedAt = 0 dia .........: {zerados} ({zerados / len(update) * 100:.1f}%)")
    print(f"  amplitude do updatedAt .....................: {min(update)} a {max(update)} dias")
    print(f"  amplitude do pushedAt ......................: {min(push)} a {max(push)} dias")
    print("  o updatedAt varia 2 dias em toda a base e o pushedAt varia mais de")
    print("  6 anos: reportar o updatedAt como resposta da RQ04 seria reportar um")
    print("  artefato da API, e nao uma caracteristica dos sistemas estudados.")

    return update, push


def secao_descritiva(push):
    d = descritiva(push)
    _, cerca_alta = limites_de_tukey(push)
    outliers = sum(1 for v in push if v > cerca_alta)

    print("\n=== RQ04.2 - valores centrais do tempo desde o ultimo push ===")
    print(f"  n ..........................................: {d['n']}")
    print(f"  mediana ....................................: {d['mediana']:.0f} dias")
    print(f"  media ......................................: {d['media']:.1f} dias")
    print(f"  Q1 / Q3 ....................................: {d['q1']:.0f} / {d['q3']:.0f}")
    print(f"  IQR ........................................: {d['iqr']:.0f}")
    print(f"  minimo / maximo ............................: {d['min']} / {d['max']}")
    print(f"  cerca superior de Tukey (Q3 + 1,5 x IQR) ...: {cerca_alta:.0f}")
    print(f"  outliers superiores ........................: {outliers} ({outliers / d['n'] * 100:.1f}%)")
    print("  metade da base recebeu push em 2 dias ou menos, mas a cauda chega a")
    print("  mais de 6 anos - os outliers sao os projetos que a popularidade")
    print("  sobreviveu ao desenvolvimento.")

    return d


def secao_categorias(update, push):
    linhas_update = contar_por_faixa(update, FAIXAS_DIAS)
    linhas_push = contar_por_faixa(push, FAIXAS_DIAS)

    print("\n=== RQ04.3 - contagem por categoria ===")
    print(f"  {'faixa':20s} {'updatedAt':>18s} {'pushedAt':>18s}")
    for (rotulo, qu, pu), (_, qp, pp) in zip(linhas_update, linhas_push):
        print(f"  {rotulo:20s} {qu:9d} ({pu:5.1f}%) {qp:9d} ({pp:5.1f}%)")

    abandonados = sum(1 for v in push if v > CORTE_ABANDONO)
    ativos = sum(1 for v in push if v <= 30)
    print(f"  ativos (push nos ultimos 30 dias) ..........: {ativos} ({ativos / len(push) * 100:.1f}%)")
    print(f"  parados (mais de {CORTE_ABANDONO} dias sem push) ........: {abandonados} ({abandonados / len(push) * 100:.1f}%)")

    return linhas_update, linhas_push


def secao_extremos(repos):
    print("\n=== RQ04.4 - repositorios mais tempo sem push ===")
    piores = sorted(repos, key=lambda r: -r["dias_push"])[:10]
    for r in piores:
        anos = r["dias_push"] / 365.25
        print(f"    {r['nome']:48s} {r['dias_push']:>5d} dias ({anos:.1f} anos) "
              f"{r['estrelas']:>7d} estrelas")
    print("  sao listas, roteiros de estudo e software descontinuado que")
    print("  continuam no top 1000 por estrela acumulada - a estrela nunca")
    print("  decresce, o codigo para.")
    return piores


# ---------------------------------------------------------------------------
# Graficos
# ---------------------------------------------------------------------------
def grafico_comparacao(linhas_update, linhas_push):
    fig, ax = nova_figura(
        "RQ04 - Por que a metrica do enunciado foi trocada",
        "Mesma base, mesmas faixas, dois campos da API. O updatedAt coloca 100% "
        "dos repositorios em 'ate 7 dias'; o pushedAt separa a base.",
        tamanho=(9.4, 5.4),
    )
    fig.subplots_adjust(top=0.76, bottom=0.16, left=0.065, right=0.985)

    rotulos = [l[0] for l in linhas_update]
    posicoes = range(len(rotulos))
    largura = 0.38

    grade(ax, "y")
    barras_update = ax.bar(
        [p - largura / 2 - 0.01 for p in posicoes], [l[1] for l in linhas_update],
        width=largura, color=SERIE_2, zorder=2,
    )
    barras_push = ax.bar(
        [p + largura / 2 + 0.01 for p in posicoes], [l[1] for l in linhas_push],
        width=largura, color=SERIE_1, zorder=2,
    )

    ax.set_xticks(list(posicoes))
    ax.set_xticklabels(rotulos, fontsize=9, color=TINTA_MEDIA)
    ax.set_ylim(0, 1000 * 1.14)
    ax.set_xlabel("Tempo desde a ultima atualizacao", fontsize=9.5,
                  color=TINTA_MEDIA, labelpad=8)
    ax.set_ylabel("Repositorios", fontsize=9.5, color=TINTA_MEDIA, labelpad=8)

    legenda(ax, [
        (SERIE_2, "dias desde updatedAt (metrica literal do enunciado)"),
        (SERIE_1, "dias desde pushedAt (metrica efetiva adotada)"),
    ], loc="upper right")

    for barras, linhas in ((barras_update, linhas_update), (barras_push, linhas_push)):
        rotular_barras(ax, barras, [f"{l[1]}" for l in linhas])
        arredondar_pontas(ax, barras)

    return salvar(fig, "rq04_updatedat_x_pushedat.png")


def grafico_ecdf(push, d):
    fig, ax = nova_figura(
        "RQ04 - Distribuicao cumulativa do tempo desde o ultimo push",
        "43,7% dos repositorios receberam push no proprio dia da coleta.\n"
        "A cauda vai a 6,7 anos: 11,5% esta ha mais de um ano sem push.",
        tamanho=(9.2, 5.3),
    )
    fig.subplots_adjust(top=0.73, bottom=0.16, left=0.075, right=0.985)

    xs, ys = ecdf([max(v, 0) for v in push])

    grade(ax, "y")
    ax.set_xscale("symlog", linthresh=1)
    ax.plot(xs, ys, color=SERIE_1, linewidth=2.0, zorder=3, solid_capstyle="round")
    ax.set_xlim(0, max(xs) * 1.3)
    ax.set_ylim(0, 100)
    ax.set_xlabel("Dias desde o ultimo push (escala log)", fontsize=9.5,
                  color=TINTA_MEDIA, labelpad=8)
    ax.set_ylabel("Percentual acumulado dos 1.000 repositorios", fontsize=9.5,
                  color=TINTA_MEDIA, labelpad=8)

    for valor, rotulo in ((d["mediana"], "mediana"), (d["q3"], "Q3")):
        ax.axvline(valor, color=DESTAQUE, linewidth=1.2, linestyle=(0, (4, 3)), zorder=2)
        ax.annotate(
            f"{rotulo} = {valor:.0f} dias",
            xy=(valor, 6), xytext=(valor * 1.35, 6),
            fontsize=9, color=DESTAQUE,
        )

    ax.axvline(CORTE_ABANDONO, color=TINTA_FRACA, linewidth=1.2, zorder=2)
    parados = sum(1 for v in push if v > CORTE_ABANDONO)
    ax.annotate(
        f"1 ano sem push\n{parados} repositorios acima "
        f"({br(parados / len(push) * 100)}%)",
        xy=(CORTE_ABANDONO, 30), xytext=(CORTE_ABANDONO * 0.85, 30),
        fontsize=9, color=TINTA_FRACA, ha="right",
    )

    return salvar(fig, "rq04_ecdf_dias_sem_push.png")


def grafico_extremos(piores):
    fig, ax = nova_figura(
        "RQ04 - Os 10 repositorios do top 1000 com mais tempo sem push",
        "Estrela e metrica de acervo: ela nao decresce quando o projeto para. "
        "Todos estes seguem entre os 1.000 mais estrelados do GitHub.",
        tamanho=(9.6, 5.6),
    )
    fig.subplots_adjust(top=0.78, bottom=0.13, left=0.40, right=0.905)

    nomes = [r["nome"] for r in piores][::-1]
    valores = [r["dias_push"] / 365.25 for r in piores][::-1]

    grade(ax, "x")
    barras = ax.barh(nomes, valores, height=0.62, color=SERIE_1, zorder=2)
    ax.set_xlim(0, max(valores) * 1.16)
    ax.set_xlabel("Anos desde o ultimo push", fontsize=9.5, color=TINTA_MEDIA, labelpad=8)
    ax.tick_params(axis="y", labelsize=9)

    rotular_barras(
        ax, barras,
        [f"{br(v)} anos" for v in valores],
        horizontal=True, folga=0.015,
    )
    arredondar_pontas(ax, barras, horizontal=True)

    return salvar(fig, "rq04_mais_tempo_sem_push.png")


def main():
    try:
        repos, referencia = carregar_base()
    except (FileNotFoundError, ValueError) as erro:
        sys.exit(f"{erro}\nRode src/fetch_repos.py primeiro.")

    print("RQ04 - Sistemas populares sao atualizados com frequencia?")
    print(f"Base: data/repositorios_top1000.csv  |  coleta de {referencia:%Y-%m-%d}\n")

    update, push = secao_comparacao(repos)
    d = secao_descritiva(push)
    linhas_update, linhas_push = secao_categorias(update, push)
    piores = secao_extremos(repos)

    print("\n=== Graficos gerados ===")
    for caminho in (
        grafico_comparacao(linhas_update, linhas_push),
        grafico_ecdf(push, d),
        grafico_extremos(piores),
    ):
        print(f"  {caminho}")

    print("\nAnalise da RQ04 concluida.")


if __name__ == "__main__":
    main()
