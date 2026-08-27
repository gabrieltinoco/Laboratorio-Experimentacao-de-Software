"""
Lab01S03 - base comum da analise e visualizacao das RQs.

Concentra tres coisas que as tres analises da S03 (RQ03, RQ04 e RQ09) usam do
mesmo jeito, para que os numeros do relatorio e os graficos nunca divirjam:

1. Carga do CSV com as colunas derivadas (idade, cadencia) ja calculadas.
2. Estatistica descritiva e correlacao de postos, escritas na mao.
3. Estilo dos graficos, com paleta validada para daltonismo.

Sobre a data de referencia: as colunas `dias_desde_*` do CSV foram calculadas no
momento da coleta, mas a idade nao esta no CSV e precisa ser derivada de
`created_at`. Se derivarmos usando `datetime.now()`, a idade cresce a cada
execucao e os numeros do relatorio deixam de ser reproduziveis. Por isso a data
de referencia e reconstruida a partir do proprio CSV
(`ultima_atualizacao + dias_desde_ultima_atualizacao`), que devolve o instante da
coleta: 2026-08-19T15:14:50Z. Rodar a analise hoje ou em um ano da o mesmo
resultado.

Este modulo nao consulta a API do GitHub. A unica dependencia externa e o
matplotlib, usado apenas para desenhar; a estatistica e toda propria.
"""

import csv
import statistics
from datetime import datetime, timedelta, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # sem janela: a saida da S03 e arquivo PNG

import matplotlib.pyplot as plt
from matplotlib.patches import Patch, PathPatch
from matplotlib.path import Path as MplPath

RAIZ = Path(__file__).resolve().parent.parent
CSV_PATH = RAIZ / "data" / "repositorios_top1000.csv"
GRAFICOS_DIR = RAIZ / "graficos"

FORMATO_DATA = "%Y-%m-%dT%H:%M:%SZ"
DIAS_POR_ANO = 365.25

# Valor que a coleta grava quando `primaryLanguage` vem nulo da API (ver
# src/fetch_repos.py). Nao e uma linguagem: e a ausencia de codigo predominante
# detectado, e por isso vira None aqui.
SEM_LINGUAGEM = "Nao informada"

# Teto do campo releases.totalCount na API do GitHub, ja identificado na
# validacao da S02: nesses repositorios o total e limite inferior, nao valor
# real, e precisa ser sinalizado em todo grafico da RQ03 e da RQ09.
TETO_RELEASES = 1000

# ---------------------------------------------------------------------------
# Paleta
# ---------------------------------------------------------------------------
# Paleta categorica validada para visao normal e para as tres formas de
# daltonismo (deutan, protan, tritan): pior par com diferenca perceptual de
# 9,2 em CVD e 24,0 em visao normal, ambos acima do piso exigido. Os graficos
# usam no maximo tres series justamente porque e ate tres que a paleta passa em
# todos os pares. Alem da cor, toda serie leva rotulo direto, entao a leitura
# nunca depende de cor sozinha.
SERIE_1 = "#2a78d6"  # azul
SERIE_2 = "#eb6834"  # laranja
SERIE_3 = "#1baf7a"  # verde-agua

# Rampa ordinal de um unico tom (azul, claro -> escuro), para as faixas de
# idade e de tempo, onde a ordem das categorias tem significado.
RAMPA_ORDINAL = ["#86b6ef", "#5598e7", "#2a78d6", "#184f95"]

SUPERFICIE = "#fcfcfb"
TINTA_FORTE = "#0b0b0b"
TINTA_MEDIA = "#52514e"
TINTA_FRACA = "#8a8880"
GRADE = "#e7e6e2"
DESTAQUE = "#e34948"  # vermelho reservado para marcar mediana e teto da API

FONTE_PADRAO = (
    "Fonte: 1.000 repositorios mais estrelados do GitHub, "
    "coleta de 2026-08-19 (data/repositorios_top1000.csv)."
)


# ---------------------------------------------------------------------------
# Carga
# ---------------------------------------------------------------------------
def data_de_referencia(rows):
    """Reconstroi o instante da coleta a partir do proprio CSV.

    Cada linha carrega a data bruta (`ultima_atualizacao`) e os dias decorridos
    calculados na coleta. Somar um ao outro devolve o dia da coleta; o maximo
    entre as 1000 linhas e o instante mais tardio compativel com todas elas.
    """
    candidatos = [
        datetime.strptime(r["ultima_atualizacao"], FORMATO_DATA)
        + timedelta(days=int(r["dias_desde_ultima_atualizacao"]))
        for r in rows
        if r["ultima_atualizacao"] and r["dias_desde_ultima_atualizacao"]
    ]
    return max(candidatos).replace(tzinfo=timezone.utc)


def carregar_base(path=CSV_PATH):
    """Le o CSV e devolve (repositorios, data_de_referencia).

    Cada repositorio e um dict com os campos brutos convertidos e as colunas
    derivadas que as RQs da S03 precisam.
    """
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        raise ValueError(f"{path} esta vazio.")

    referencia = data_de_referencia(rows)
    repos = []

    for row in rows:
        criado = datetime.strptime(row["created_at"], FORMATO_DATA)
        criado = criado.replace(tzinfo=timezone.utc)
        idade = (referencia - criado).days / DIAS_POR_ANO
        releases = int(row["total_releases"])
        linguagem = row["linguagem_primaria"].strip()

        repos.append({
            "nome": row["repositorio"],
            "estrelas": int(row["estrelas"]),
            "linguagem": linguagem if linguagem and linguagem != SEM_LINGUAGEM else None,
            "criado_em": criado,
            "idade": idade,
            "releases": releases,
            "no_teto": releases >= TETO_RELEASES,
            # Sem release, a cadencia nao esta definida - e ausencia de
            # versionamento publicado, nao cadencia zero. Fica None de
            # proposito, para nao entrar como zero na mediana.
            "cadencia": releases / idade if releases > 0 and idade > 0 else None,
            "dias_update": int(row["dias_desde_ultima_atualizacao"]),
            "dias_push": int(row["dias_desde_ultimo_push"]),
        })

    return repos, referencia


# ---------------------------------------------------------------------------
# Estatistica
# ---------------------------------------------------------------------------
def descritiva(valores):
    """Mediana, media, quartis, IQR, minimo e maximo de uma lista."""
    q1, _, q3 = statistics.quantiles(valores, n=4)
    return {
        "n": len(valores),
        "mediana": statistics.median(valores),
        "media": statistics.mean(valores),
        "q1": q1,
        "q3": q3,
        "iqr": q3 - q1,
        "min": min(valores),
        "max": max(valores),
    }


def limites_de_tukey(valores):
    """Cercas de Tukey (1,5 x IQR), o critorio de outlier usado no laboratorio."""
    d = descritiva(valores)
    return d["q1"] - 1.5 * d["iqr"], d["q3"] + 1.5 * d["iqr"]


def postos(valores):
    """Postos de 1 a n, com media dos postos em caso de empate."""
    ordem = sorted(range(len(valores)), key=lambda i: valores[i])
    resultado = [0.0] * len(valores)

    i = 0
    while i < len(ordem):
        j = i
        while j + 1 < len(ordem) and valores[ordem[j + 1]] == valores[ordem[i]]:
            j += 1
        media_posto = (i + j) / 2 + 1
        for k in range(i, j + 1):
            resultado[ordem[k]] = media_posto
        i = j + 1

    return resultado


def correlacao_de_postos(x, y):
    """Correlacao de Spearman, calculada na mao para nao depender de biblioteca.

    E a correlacao de Pearson aplicada sobre os postos. Usamos a de postos, e
    nao a linear, porque as duas variaveis tem cauda longa e outliers extremos,
    que dominariam uma correlacao linear.
    """
    px, py = postos(x), postos(y)
    mx, my = statistics.mean(px), statistics.mean(py)

    numerador = sum((a - mx) * (b - my) for a, b in zip(px, py))
    denominador = (
        sum((a - mx) ** 2 for a in px) * sum((b - my) ** 2 for b in py)
    ) ** 0.5

    return numerador / denominador if denominador else 0.0


def limite_de_significancia(n):
    """Valor de correlacao a partir do qual o resultado nao e ruido, a 5%.

    Aproximacao valida para amostra grande: |r| > 1,96 / raiz(n - 1). Serve para
    dizer se a correlacao encontrada e forte o suficiente para o tamanho da
    amostra, sem precisar de biblioteca de estatistica.
    """
    return 1.96 / ((n - 1) ** 0.5) if n > 2 else float("inf")


def br(valor, decimais=1):
    """Numero no padrao brasileiro: virgula decimal e ponto de milhar.

    Os rotulos dos graficos vao para um relatorio em portugues, entao o separador
    tem de ser o virgula - o padrao do matplotlib e o ponto.
    """
    texto = f"{valor:,.{decimais}f}"
    return texto.replace(",", " ").replace(".", ",").replace(" ", ".")


def em_faixa(valor, minimo, maximo):
    """Pertencimento a uma faixa com extremos opcionalmente abertos."""
    if minimo is None:
        return valor <= maximo
    if maximo is None:
        return valor >= minimo
    return minimo <= valor <= maximo


def contar_por_faixa(valores, faixas):
    """[(rotulo, quantidade, percentual)] para uma lista de faixas."""
    total = len(valores)
    linhas = []
    for rotulo, minimo, maximo in faixas:
        qtd = sum(1 for v in valores if em_faixa(v, minimo, maximo))
        linhas.append((rotulo, qtd, qtd / total * 100))
    return linhas


def ecdf(valores):
    """Distribuicao cumulativa empirica: (valores ordenados, percentual <= v).

    Usada em vez de histograma quando a variavel tem cauda longa: a curva mostra
    a mediana e os quartis diretamente, sem depender da escolha de largura de
    bin.
    """
    ordenados = sorted(valores)
    n = len(ordenados)
    return ordenados, [(i + 1) / n * 100 for i in range(n)]


# ---------------------------------------------------------------------------
# Graficos
# ---------------------------------------------------------------------------
def nova_figura(titulo, subtitulo=None, tamanho=(9.0, 5.2), colunas=1):
    """Figura com o estilo unico dos graficos do laboratorio.

    Grade e eixos recessivos, sem moldura, titulo alinhado a esquerda e
    subtitulo em tinta media - a hierarquia fica no texto, nao na cor das
    marcas.
    """
    fig, eixos = plt.subplots(1, colunas, figsize=tamanho, facecolor=SUPERFICIE)
    lista = [eixos] if colunas == 1 else list(eixos)

    for ax in lista:
        ax.set_facecolor(SUPERFICIE)
        for lado in ("top", "right"):
            ax.spines[lado].set_visible(False)
        for lado in ("left", "bottom"):
            ax.spines[lado].set_color(GRADE)
        ax.tick_params(colors=TINTA_MEDIA, labelsize=9, length=0)

    fig.suptitle(
        titulo, x=0.012, y=0.975, ha="left", va="top",
        fontsize=13.5, color=TINTA_FORTE, fontweight="bold",
    )
    if subtitulo:
        fig.text(
            0.012, 0.902, subtitulo, ha="left", va="top",
            fontsize=9.5, color=TINTA_MEDIA,
        )

    return fig, (lista[0] if colunas == 1 else lista)


def grade(ax, eixo="y"):
    """Grade de referencia atras das marcas, no eixo de valor apenas."""
    ax.grid(axis=eixo, color=GRADE, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)


def _raio_em_dados(ax, eixo, pixels=4.0):
    """Converte um raio em pixels para unidades de dados do eixo pedido."""
    ax.figure.canvas.draw()
    caixa = ax.get_window_extent()
    if eixo == "x":
        lo, hi = ax.get_xlim()
        extensao_px = caixa.width
    else:
        lo, hi = ax.get_ylim()
        extensao_px = caixa.height
    return abs(hi - lo) * pixels / extensao_px if extensao_px else 0.0


def arredondar_pontas(ax, barras, horizontal=False, pixels=4.0):
    """Arredonda so a ponta de dado das barras, deixando a base na linha zero.

    A ponta arredondada e o detalhe que distingue o fim do dado do fim do eixo;
    a base fica reta porque ela e a linha de referencia, nao um valor. Precisa
    ser chamada depois de os limites do eixo estarem definidos.
    """
    rx = _raio_em_dados(ax, "x", pixels)
    ry = _raio_em_dados(ax, "y", pixels)

    for barra in barras:
        x0, y0 = barra.get_x(), barra.get_y()
        largura, altura = barra.get_width(), barra.get_height()
        cor = barra.get_facecolor()
        x1, y1 = x0 + largura, y0 + altura

        if horizontal:
            r = min(rx, largura / 2) if largura > 0 else 0.0
            ry_local = min(ry, altura / 2)
            vertices = [
                (x0, y0), (x1 - r, y0), (x1, y0), (x1, y0 + ry_local),
                (x1, y1 - ry_local), (x1, y1), (x1 - r, y1), (x0, y1), (x0, y0),
            ]
        else:
            r = min(ry, altura / 2) if altura > 0 else 0.0
            rx_local = min(rx, largura / 2)
            vertices = [
                (x0, y0), (x0, y1 - r), (x0, y1), (x0 + rx_local, y1),
                (x1 - rx_local, y1), (x1, y1), (x1, y1 - r), (x1, y0), (x0, y0),
            ]

        codigos = [
            MplPath.MOVETO, MplPath.LINETO, MplPath.CURVE3, MplPath.CURVE3,
            MplPath.LINETO, MplPath.CURVE3, MplPath.CURVE3,
            MplPath.LINETO, MplPath.CLOSEPOLY,
        ]

        barra.set_visible(False)
        ax.add_patch(PathPatch(
            MplPath(vertices, codigos),
            facecolor=cor, edgecolor="none", zorder=barra.get_zorder(),
        ))


def rotular_barras(ax, barras, textos, horizontal=False, folga=0.012):
    """Rotulo direto no fim de cada barra.

    Os rotulos nao sao decoracao: a paleta tem um tom com contraste abaixo de
    3:1 na superficie clara, e a regra de acessibilidade adotada exige que,
    nesse caso, o valor apareca escrito. Como o PNG nao tem tooltip, o rotulo
    direto e a tabela do relatorio fazem esse papel.
    """
    lo, hi = (ax.get_xlim() if horizontal else ax.get_ylim())
    deslocamento = (hi - lo) * folga

    for barra, texto in zip(barras, textos):
        if horizontal:
            ax.text(
                barra.get_width() + deslocamento,
                barra.get_y() + barra.get_height() / 2,
                texto, va="center", ha="left",
                fontsize=9, color=TINTA_MEDIA,
            )
        else:
            ax.text(
                barra.get_x() + barra.get_width() / 2,
                barra.get_height() + deslocamento,
                texto, ha="center", va="bottom",
                fontsize=9, color=TINTA_MEDIA,
            )


def legenda(ax, series, **kwargs):
    """Legenda sem moldura, obrigatoria sempre que houver duas ou mais series.

    `series` e uma lista de (cor, rotulo). Usamos marcas proxy em vez das marcas
    do proprio grafico porque `arredondar_pontas` substitui as barras originais
    por outro objeto, e a legenda montada a partir delas sairia sem cor.
    """
    alcas = [Patch(facecolor=cor, edgecolor="none", label=rotulo)
             for cor, rotulo in series]
    return ax.legend(
        handles=alcas, frameon=False, fontsize=9, labelcolor=TINTA_MEDIA,
        handlelength=1.0, handleheight=0.9, borderpad=0.0,
        labelspacing=0.7, **kwargs,
    )


def salvar(fig, nome, fonte=None):
    """Grava o PNG em graficos/ e devolve o caminho relativo a Laboratorio01."""
    fig.text(0.012, 0.018, fonte or FONTE_PADRAO, ha="left", va="bottom",
             fontsize=8, color=TINTA_FRACA)

    GRAFICOS_DIR.mkdir(exist_ok=True)
    destino = GRAFICOS_DIR / nome
    fig.savefig(destino, dpi=160, facecolor=SUPERFICIE)
    plt.close(fig)
    return destino.relative_to(RAIZ).as_posix()
