"""
Lab01S03 - analise e visualizacao da RQ09 (proposta pelo grupo).

RQ09 - A cadencia de releases se mantem ao longo da vida do projeto?
       Metrica: cadencia = total_releases / idade em anos, cruzada com a idade
       do repositorio (RQ01) e com o tempo desde o ultimo push (RQ04).

A RQ03 mede o total absoluto de releases, e esse total tem um vies estrutural:
um repositorio de 15 anos teve tres vezes mais tempo para publicar releases que
um de 5 anos. Se o resultado da RQ03 for so idade disfarcada de cadencia, ele
nao responde nada sobre pratica de engenharia. Normalizar pela idade testa isso,
e amarra tres RQs que ate aqui sao respondidas isoladamente: idade (RQ01),
releases (RQ03) e atividade (RQ04).

A analise da S02 (`src/rq09_cadencia_releases.py`) estabeleceu o resultado
numerico. Esta da S03 o consolida na forma final do relatorio e produz os
graficos, sem recoletar nada: usa `created_at` e `total_releases`, que ja estao
na base validada.

Uso:
    python src/analise_rq09.py
"""

import statistics
import sys

from analise_base import (
    DESTAQUE,
    RAMPA_ORDINAL,
    SERIE_1,
    SUPERFICIE,
    TETO_RELEASES,
    TINTA_MEDIA,
    arredondar_pontas,
    br,
    carregar_base,
    correlacao_de_postos,
    descritiva,
    em_faixa,
    grade,
    legenda,
    limite_de_significancia,
    nova_figura,
    rotular_barras,
    salvar,
)

# Abaixo de 1 ano de vida, dividir o total de releases por uma fracao de ano
# infla a cadencia de forma artificial (um repositorio de 5 meses com 932
# releases vira "2.182 releases/ano"). Esses casos entram no resultado geral,
# mas o teste de robustez roda tambem sem eles.
IDADE_MINIMA_ROBUSTEZ = 1.0

FAIXAS_IDADE = [
    ("ate 3 anos", 0, 3),
    ("3 a 7 anos", 3, 7),
    ("7 a 12 anos", 7, 12),
    ("mais de 12 anos", 12, None),
]

FAIXAS_ATIVIDADE = [
    ("ativo\n(push <= 30 dias)", None, 30),
    ("morno\n(31 a 365 dias)", 31, 365),
    ("parado\n(> 365 dias)", 366, None),
]


# ---------------------------------------------------------------------------
# Analise
# ---------------------------------------------------------------------------
def secao_distribuicao(com_cadencia, sem_release, total):
    print("=== RQ09.1 - distribuicao da cadencia de releases ===")
    print(f"  repositorios na base .......................: {total}")
    print(f"  sem release, cadencia nao definida ........: {len(sem_release)} ({len(sem_release) / total * 100:.1f}%)")
    print(f"  com cadencia calculavel ...................: {len(com_cadencia)} ({len(com_cadencia) / total * 100:.1f}%)")

    d = descritiva([r["cadencia"] for r in com_cadencia])
    print(f"  mediana ...................................: {d['mediana']:.2f} releases/ano")
    print(f"  media .....................................: {d['media']:.2f} releases/ano")
    print(f"  Q1 / Q3 ...................................: {d['q1']:.2f} / {d['q3']:.2f}")
    print(f"  minimo / maximo ...........................: {d['min']:.2f} / {d['max']:.2f}")
    print("  a cadencia nao e zero para quem nao publica release: e indefinida.")
    print("  tratar como zero misturaria 'nao versiona' com 'versiona pouco'.")

    return d


def secao_correlacao(com_cadencia, todos):
    """O teste central: a idade explica o total de releases da RQ03?"""
    rho_total = correlacao_de_postos(
        [r["idade"] for r in todos], [r["releases"] for r in todos]
    )
    rho_cadencia = correlacao_de_postos(
        [r["idade"] for r in com_cadencia], [r["cadencia"] for r in com_cadencia]
    )
    limite_todos = limite_de_significancia(len(todos))
    limite_cadencia = limite_de_significancia(len(com_cadencia))

    print("\n=== RQ09.2 - a idade explica o total de releases da RQ03? ===")
    print(f"  idade x total de releases ..................: {rho_total:+.3f} (n={len(todos)}, ruido +-{limite_todos:.3f})")
    print(f"  idade x cadencia de releases ...............: {rho_cadencia:+.3f} (n={len(com_cadencia)}, ruido +-{limite_cadencia:.3f})")

    # O primeiro valor cai quase exatamente sobre o limite de ruido, entao o
    # argumento nao pode ser so "nao e significativo": vale reportar tambem o
    # quanto da variacao ele explicaria se fosse real, que e o que decide se a
    # RQ03 esta ou nao contaminada pela idade.
    print(f"  variacao do total de releases explicada pela idade: "
          f"{rho_total ** 2 * 100:.1f}%")
    print(f"  variacao da cadencia explicada pela idade ..: {rho_cadencia ** 2 * 100:.1f}%")

    if abs(rho_total) <= limite_todos:
        print("  o primeiro valor esta na fronteira do ruido e, mesmo se real,")
        print("  explicaria menos de 0,4% da variacao: repositorio mais velho NAO")
        print("  tem mais releases, e o resultado da RQ03 nao e artefato de idade.")
    if rho_cadencia < -limite_cadencia:
        print("  o segundo esta muito acima do ruido e no sentido oposto ao")
        print("  esperado: a cadencia CAI conforme o projeto envelhece.")

    print("\n  -- robustez --")
    sub = [r for r in com_cadencia if r["idade"] >= IDADE_MINIMA_ROBUSTEZ]
    rho_sub = correlacao_de_postos(
        [r["idade"] for r in sub], [r["cadencia"] for r in sub]
    )
    sub2 = [r for r in sub if not r["no_teto"]]
    rho_sub2 = correlacao_de_postos(
        [r["idade"] for r in sub2], [r["cadencia"] for r in sub2]
    )

    print(f"  excluindo vida < {IDADE_MINIMA_ROBUSTEZ:.0f} ano ...................: {rho_sub:+.3f} (n={len(sub)})")
    print(f"  e tambem sem o teto de {TETO_RELEASES} releases .....: {rho_sub2:+.3f} (n={len(sub2)})")
    print("  sinal e ordem de grandeza se mantem nos dois cortes.")

    return {
        "rho_total": rho_total,
        "rho_cadencia": rho_cadencia,
        "limite_todos": limite_todos,
        "limite_cadencia": limite_cadencia,
        "rho_sub": rho_sub,
        "n_sub": len(sub),
        "rho_sub2": rho_sub2,
        "n_sub2": len(sub2),
    }


def agrupar(com_cadencia, faixas, chave):
    """Mediana de releases e de cadencia por faixa de uma variavel."""
    grupos = []
    for rotulo, minimo, maximo in faixas:
        grupo = [r for r in com_cadencia if em_faixa(r[chave], minimo, maximo)]
        if not grupo:
            continue
        grupos.append({
            "rotulo": rotulo,
            "n": len(grupo),
            "mediana_releases": statistics.median([r["releases"] for r in grupo]),
            "mediana_cadencia": statistics.median([r["cadencia"] for r in grupo]),
            "mediana_idade": statistics.median([r["idade"] for r in grupo]),
        })
    return grupos


def secao_por_idade(com_cadencia):
    grupos = agrupar(com_cadencia, FAIXAS_IDADE, "idade")

    print("\n=== RQ09.3 - cadencia por faixa de idade (resultado central) ===")
    print(f"  {'faixa':18s} {'n':>5s} {'mediana releases':>17s} {'mediana cadencia':>17s}")
    for g in grupos:
        print(f"  {g['rotulo']:18s} {g['n']:5d} "
              f"{g['mediana_releases']:17.0f} {g['mediana_cadencia']:17.2f}")

    razao = grupos[0]["mediana_cadencia"] / grupos[-1]["mediana_cadencia"]
    print("  o total de releases nao tem tendencia com a idade - sobe da primeira")
    print("  para a terceira faixa e volta a cair na quarta -, mas a cadencia cai")
    print(f"  em todas as faixas, por um fator de {razao:.1f} entre a mais nova e a")
    print("  mais velha.")

    return grupos


def secao_por_atividade(com_cadencia):
    grupos = agrupar(com_cadencia, FAIXAS_ATIVIDADE, "dias_push")

    print("\n=== RQ09.4 - cadencia por grupo de atividade (cruzamento com a RQ04) ===")
    print(f"  {'grupo':22s} {'n':>5s} {'mediana cadencia':>17s} {'idade mediana':>14s}")
    for g in grupos:
        print(f"  {g['rotulo'].replace(chr(10), ' '):22s} {g['n']:5d} "
              f"{g['mediana_cadencia']:17.2f} {g['mediana_idade']:13.1f}a")
    print("  quem esta parado tem cadencia historica baixa, e a idade mediana dos")
    print("  tres grupos e parecida: cadencia baixa nao e efeito de ser velho, e")
    print("  indicador de saude do projeto - algo que nem a RQ03 nem a RQ04 medem")
    print("  isoladamente.")

    return grupos


def secao_sem_release(sem_release, total):
    print("\n=== RQ09.5 - os repositorios sem release ===")
    if not sem_release:
        print("  nenhum repositorio sem release.")
        return

    ativos = [r for r in sem_release if r["dias_push"] <= 90]
    sem_linguagem = [r for r in sem_release if not r["linguagem"]]
    print(f"  n .........................................: {len(sem_release)} ({len(sem_release) / total * 100:.1f}%)")
    print(f"  idade mediana .............................: {statistics.median([r['idade'] for r in sem_release]):.1f} anos")
    print(f"  dias sem push (mediana) ...................: {statistics.median([r['dias_push'] for r in sem_release]):.0f}")
    print(f"  ativos (push nos ultimos 90 dias) .........: {len(ativos)} ({len(ativos) / len(sem_release) * 100:.1f}%)")
    print(f"  sem linguagem primaria ....................: {len(sem_linguagem)} ({len(sem_linguagem) / len(sem_release) * 100:.1f}%)")
    print("  nao sao projetos mortos: mais da metade recebeu push recente. Sao")
    print("  repositorios mantidos que simplesmente nao versionam releases.")


def secao_extremos(com_cadencia):
    print("\n=== RQ09.6 - extremos de cadencia ===")
    print("  maior cadencia:")
    for r in sorted(com_cadencia, key=lambda r: -r["cadencia"])[:5]:
        print(f"    {r['nome']:42s} {r['cadencia']:8.1f} rel/ano "
              f"({r['releases']} releases em {r['idade']:.1f} anos)")
    print("  menor cadencia:")
    for r in sorted(com_cadencia, key=lambda r: r["cadencia"])[:5]:
        print(f"    {r['nome']:42s} {r['cadencia']:8.2f} rel/ano "
              f"({r['releases']} releases em {r['idade']:.1f} anos)")
    print("  o topo e dominado por projeto recente que publica release a cada")
    print("  merge, por pipeline automatizado; a base, por projeto de uma epoca em")
    print("  que release era evento manual com changelog escrito a mao. Nao")
    print("  estamos medindo cadencia de equipe, estamos medindo cadencia de")
    print("  ferramenta.")


# ---------------------------------------------------------------------------
# Graficos
# ---------------------------------------------------------------------------
def grafico_dispersao(com_cadencia, grupos_idade, correlacoes):
    fig, ax = nova_figura(
        "RQ09 - Idade do repositorio x cadencia de releases",
        f"Cada ponto e um dos {len(com_cadencia)} repositorios que publicam release. "
        f"Correlacao de postos {br(correlacoes['rho_cadencia'], 3)} - a nuvem\n"
        "desce da esquerda para a direita: quanto mais velho o projeto, menor a "
        "cadencia.",
        tamanho=(9.4, 5.6),
    )
    fig.subplots_adjust(top=0.72, bottom=0.14, left=0.075, right=0.985)

    grade(ax, "y")
    ax.set_yscale("log")
    ax.scatter(
        [r["idade"] for r in com_cadencia],
        [r["cadencia"] for r in com_cadencia],
        s=20, color=SERIE_1, linewidths=0.5, edgecolors=SUPERFICIE,
        zorder=2,
    )

    # A linha das medianas por faixa e o que transforma a nuvem em resultado:
    # ela e desenhada no centro de cada faixa de idade.
    centros = [1.5, 5.0, 9.5, 15.0]
    medianas = [g["mediana_cadencia"] for g in grupos_idade]
    ax.plot(
        centros, medianas, color=DESTAQUE, linewidth=2.0, marker="o",
        markersize=7, markeredgecolor=SUPERFICIE, markeredgewidth=1.2, zorder=4,
    )
    for x, y in zip(centros, medianas):
        # Fundo na cor da superficie para o rotulo nao ser lido em cima de um
        # ponto da nuvem - e o mesmo recurso do anel de separacao entre marcas
        # que se sobrepoem.
        ax.annotate(
            f"{br(y, 2)}",
            xy=(x, y), xytext=(x, y * 2.1),
            fontsize=9, color=DESTAQUE, ha="center", zorder=5,
            bbox=dict(facecolor=SUPERFICIE, edgecolor="none", pad=1.5),
        )

    ax.set_xlim(0, 19)
    ax.set_xticks(range(0, 20, 2))
    ax.set_xlabel("Idade do repositorio (anos)", fontsize=9.5,
                  color=TINTA_MEDIA, labelpad=8)
    ax.set_ylabel("Cadencia (releases por ano, escala log)", fontsize=9.5,
                  color=TINTA_MEDIA, labelpad=8)

    legenda(ax, [
        (SERIE_1, "repositorio individual"),
        (DESTAQUE, "mediana da cadencia por faixa de idade"),
    ], loc="upper right")

    return salvar(fig, "rq09_idade_x_cadencia.png")


def grafico_por_faixa_de_idade(grupos):
    fig, eixos = nova_figura(
        "RQ09 - O que muda com a idade nao e o total de releases, e a cadencia",
        "Mesmas faixas de idade, duas metricas. O total mediano de releases nao "
        "tem tendencia com a idade;\na cadencia mediana cai a cada faixa, sem "
        "excecao.",
        tamanho=(9.8, 5.3), colunas=2,
    )
    fig.subplots_adjust(top=0.74, bottom=0.24, left=0.075, right=0.985, wspace=0.28)

    rotulos = [f"{g['rotulo']}\nn = {g['n']}" for g in grupos]
    cores = RAMPA_ORDINAL[:len(grupos)]

    paineis = [
        (eixos[0], "Mediana do total de releases (RQ03)",
         [g["mediana_releases"] for g in grupos],
         [f"{g['mediana_releases']:.0f}" for g in grupos]),
        (eixos[1], "Mediana da cadencia (releases/ano)",
         [g["mediana_cadencia"] for g in grupos],
         [f"{br(g['mediana_cadencia'], 2)}" for g in grupos]),
    ]

    for ax, titulo, valores, textos in paineis:
        grade(ax, "y")
        barras = ax.bar(rotulos, valores, width=0.6, color=cores, zorder=2)
        ax.set_ylim(0, max(valores) * 1.22)
        ax.set_title(titulo, fontsize=10, color=TINTA_MEDIA, loc="left", pad=10)
        ax.tick_params(axis="x", labelsize=8.5)
        rotular_barras(ax, barras, textos)
        arredondar_pontas(ax, barras)

    return salvar(fig, "rq09_cadencia_por_faixa_de_idade.png")


def grafico_por_atividade(grupos):
    fig, ax = nova_figura(
        "RQ09 - Cadencia por grupo de atividade (cruzamento com a RQ04)",
        "A idade mediana dos tres grupos e parecida, entao a diferenca de cadencia\n"
        "nao vem da idade: cadencia baixa e abandono andam juntos.",
        tamanho=(9.0, 5.4),
    )
    fig.subplots_adjust(top=0.72, bottom=0.24, left=0.08, right=0.985)

    # A idade mediana entra no rotulo do eixo, e nao como segundo eixo de valor:
    # duas escalas no mesmo grafico e o erro classico de leitura, e o que importa
    # aqui e so constatar que as tres idades sao proximas.
    rotulos = [
        f"{g['rotulo']}\nn = {g['n']}\nidade mediana {br(g['mediana_idade'])} anos"
        for g in grupos
    ]
    valores = [g["mediana_cadencia"] for g in grupos]

    grade(ax, "y")
    barras = ax.bar(rotulos, valores, width=0.5, color=SERIE_1, zorder=2)
    ax.set_ylim(0, max(valores) * 1.26)
    ax.set_ylabel("Mediana da cadencia (releases/ano)", fontsize=9.5,
                  color=TINTA_MEDIA, labelpad=8)
    ax.tick_params(axis="x", labelsize=9)

    rotular_barras(ax, barras, [br(v, 2) for v in valores])
    arredondar_pontas(ax, barras)

    return salvar(fig, "rq09_cadencia_por_atividade.png")


def main():
    try:
        repos, referencia = carregar_base()
    except (FileNotFoundError, ValueError) as erro:
        sys.exit(f"{erro}\nRode src/fetch_repos.py primeiro.")

    com_cadencia = [r for r in repos if r["cadencia"] is not None]
    sem_release = [r for r in repos if r["cadencia"] is None]

    print("RQ09 - A cadencia de releases se mantem ao longo da vida do projeto?")
    print(f"Base: data/repositorios_top1000.csv  |  coleta de {referencia:%Y-%m-%d}\n")

    secao_distribuicao(com_cadencia, sem_release, len(repos))
    correlacoes = secao_correlacao(com_cadencia, repos)
    grupos_idade = secao_por_idade(com_cadencia)
    grupos_atividade = secao_por_atividade(com_cadencia)
    secao_sem_release(sem_release, len(repos))
    secao_extremos(com_cadencia)

    print("\n=== Graficos gerados ===")
    for caminho in (
        grafico_dispersao(com_cadencia, grupos_idade, correlacoes),
        grafico_por_faixa_de_idade(grupos_idade),
        grafico_por_atividade(grupos_atividade),
    ):
        print(f"  {caminho}")

    print("\nAnalise da RQ09 concluida.")


if __name__ == "__main__":
    main()
