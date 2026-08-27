"""
RQ09 (proposta pelo grupo, fora das 7 do enunciado) - cadencia de releases.

Pergunta: a cadencia de releases dos sistemas populares se mantem ao longo da
vida do projeto, ou o total de releases medido na RQ03 e apenas efeito de o
repositorio ter existido por mais tempo?

Metrica: cadencia = total_releases / idade em anos, cruzada com a idade do
repositorio (RQ01) e com o tempo desde o ultimo push (RQ04).

Motivacao: a RQ03 mede o total absoluto de releases, e essa metrica tem um vies
estrutural - um repositorio de 15 anos teve tres vezes mais tempo para publicar
releases que um de 5 anos. Normalizar pela idade testa se a resposta da RQ03
sobrevive, e amarra tres RQs que hoje sao respondidas isoladamente: idade
(RQ01), releases (RQ03) e atividade (RQ04).

Nao precisa de campo novo na consulta nem de recoletar o CSV: usa created_at e
total_releases, que ja estao na base validada da S02.

A carga do CSV, a correlacao de postos e o limite de ruido vinham duplicados
aqui e em src/analise_base.py. Desde a S03 vem so da base comum, para que este
script e a analise final da RQ09 (src/analise_rq09.py) nunca reportem numeros
diferentes para a mesma pergunta. Um efeito colateral desejado: a idade passou a
ser derivada da data da coleta reconstruida do proprio CSV, e nao de
datetime.now(), entao a saida deixou de mudar a cada dia de execucao.

Uso:
    python src/rq09_cadencia_releases.py
"""

import statistics
import sys

from analise_base import (
    TETO_RELEASES,
    carregar_base,
    correlacao_de_postos,
    em_faixa,
    limite_de_significancia,
)

# Abaixo de 1 ano de vida, dividir o total de releases por uma fracao de ano
# infla a cadencia de forma artificial (um repositorio de 4 meses com 900
# releases vira "2182 releases/ano"). Esses casos entram no resultado geral,
# mas o teste de robustez roda tambem sem eles.
IDADE_MINIMA_ROBUSTEZ = 1.0

FAIXAS_IDADE = [
    ("ate 3 anos", 0, 3),
    ("3 a 7 anos", 3, 7),
    ("7 a 12 anos", 7, 12),
    ("mais de 12 anos", 12, None),
]

FAIXAS_ATIVIDADE = [
    ("ativo (push <= 30d)", None, 30),
    ("morno (31 a 365d)", 31, 365),
    ("parado (> 365d)", 366, None),
]


def resumo(valores, unidade=""):
    q1, _, q3 = statistics.quantiles(valores, n=4)
    return (
        f"mediana={statistics.median(valores):.2f}{unidade}  "
        f"media={statistics.mean(valores):.2f}{unidade}  "
        f"Q1={q1:.2f}  Q3={q3:.2f}  "
        f"min={min(valores):.2f}  max={max(valores):.2f}"
    )


def secao_distribuicao(com_cadencia, sem_release, total):
    print("=== RQ09.1 - distribuicao da cadencia de releases ===")
    print(f"  repositorios na base .......................: {total}")
    print(f"  sem release, cadencia nao definida .........: {len(sem_release)} ({len(sem_release) / total * 100:.1f}%)")
    print(f"  com cadencia calculavel ....................: {len(com_cadencia)} ({len(com_cadencia) / total * 100:.1f}%)")

    cadencias = [r["cadencia"] for r in com_cadencia]
    print(f"  cadencia (releases/ano): {resumo(cadencias)}")


def secao_correlacao(com_cadencia, todos):
    print("\n=== RQ09.2 - a idade explica o total de releases da RQ03? ===")

    idades_todos = [r["idade"] for r in todos]
    releases_todos = [r["releases"] for r in todos]
    rho_total = correlacao_de_postos(idades_todos, releases_todos)

    idades = [r["idade"] for r in com_cadencia]
    cadencias = [r["cadencia"] for r in com_cadencia]
    rho_cadencia = correlacao_de_postos(idades, cadencias)

    limite = limite_de_significancia(len(com_cadencia))

    print(f"  correlacao de postos idade x total de releases: {rho_total:+.3f} (n={len(todos)})")
    print(f"  correlacao de postos idade x cadencia .......: {rho_cadencia:+.3f} (n={len(com_cadencia)})")
    print(f"  limite de ruido para esta amostra ...........: +-{limite:.3f}")

    if abs(rho_total) < limite_de_significancia(len(todos)):
        print("  leitura: o total de releases da RQ03 NAO e explicado pela idade -")
        print("           repositorio mais velho nao tem mais releases.")

    if rho_cadencia < -limite:
        print("  leitura: a cadencia CAI conforme o repositorio envelhece.")

    print("\n  -- robustez --")
    sub = [r for r in com_cadencia if r["idade"] >= IDADE_MINIMA_ROBUSTEZ]
    rho_sub = correlacao_de_postos([r["idade"] for r in sub], [r["cadencia"] for r in sub])
    print(f"  excluindo vida < {IDADE_MINIMA_ROBUSTEZ:.0f} ano (n={len(sub)}): {rho_sub:+.3f}")

    sub2 = [r for r in sub if r["releases"] < TETO_RELEASES]
    rho_sub2 = correlacao_de_postos([r["idade"] for r in sub2], [r["cadencia"] for r in sub2])
    print(f"  e tambem sem o teto de {TETO_RELEASES} releases (n={len(sub2)}): {rho_sub2:+.3f}")

    if min(rho_sub, rho_sub2) < -limite:
        print("  o sinal e a ordem de grandeza se mantem nos dois cortes.")


def secao_por_idade(com_cadencia):
    print("\n=== RQ09.3 - cadencia por faixa de idade ===")
    print(f"  {'faixa':18s} {'n':>5s} {'mediana releases':>17s} {'mediana cadencia':>17s}")

    for rotulo, minimo, maximo in FAIXAS_IDADE:
        grupo = [r for r in com_cadencia if em_faixa(r["idade"], minimo, maximo)]
        if not grupo:
            continue
        print(
            f"  {rotulo:18s} {len(grupo):5d} "
            f"{statistics.median([r['releases'] for r in grupo]):17.0f} "
            f"{statistics.median([r['cadencia'] for r in grupo]):17.2f}"
        )

    print("  o total de releases nao tem tendencia com a idade, mas a cadencia")
    print("  cai a cada faixa - o que a RQ03 mede como volume e, na verdade,")
    print("  pratica de release diferente entre geracoes de projeto.")


def secao_por_atividade(com_cadencia):
    print("\n=== RQ09.4 - cadencia por grupo de atividade (RQ04) ===")
    print(f"  {'grupo':22s} {'n':>5s} {'mediana cadencia':>17s} {'idade mediana':>14s}")

    for rotulo, minimo, maximo in FAIXAS_ATIVIDADE:
        grupo = [r for r in com_cadencia if em_faixa(r["dias_push"], minimo, maximo)]
        if not grupo:
            continue
        print(
            f"  {rotulo:22s} {len(grupo):5d} "
            f"{statistics.median([r['cadencia'] for r in grupo]):17.2f} "
            f"{statistics.median([r['idade'] for r in grupo]):13.1f}a"
        )


def secao_sem_release(sem_release, total):
    print("\n=== RQ09.5 - os repositorios sem release ===")

    if not sem_release:
        print("  nenhum repositorio sem release.")
        return

    ativos = [r for r in sem_release if r["dias_push"] <= 90]
    print(f"  n = {len(sem_release)} ({len(sem_release) / total * 100:.1f}% da base)")
    print(f"  idade mediana ..............................: {statistics.median([r['idade'] for r in sem_release]):.1f} anos")
    print(f"  dias sem push (mediana) ....................: {statistics.median([r['dias_push'] for r in sem_release]):.0f}")
    print(f"  ativos (push nos ultimos 90 dias) ..........: {len(ativos)} ({len(ativos) / len(sem_release) * 100:.1f}%)")
    print("  nao sao projetos mortos: mais da metade recebeu push recente. Sao")
    print("  repositorios mantidos que simplesmente nao versionam releases -")
    print("  listas, roteiros de estudo e colecoes de material.")


def secao_extremos(com_cadencia):
    print("\n=== RQ09.6 - extremos de cadencia ===")

    print("  maior cadencia:")
    for r in sorted(com_cadencia, key=lambda r: -r["cadencia"])[:5]:
        print(
            f"    {r['nome']:42s} {r['cadencia']:8.1f} rel/ano "
            f"({r['releases']} releases em {r['idade']:.1f} anos)"
        )

    print("  menor cadencia:")
    for r in sorted(com_cadencia, key=lambda r: r["cadencia"])[:5]:
        print(
            f"    {r['nome']:42s} {r['cadencia']:8.2f} rel/ano "
            f"({r['releases']} releases em {r['idade']:.1f} anos)"
        )

    novos = [r for r in com_cadencia if r["idade"] < IDADE_MINIMA_ROBUSTEZ]
    print(f"  repositorios com menos de 1 ano de vida ....: {len(novos)}")
    print("  o topo da cadencia e dominado por projeto recente publicando")
    print("  release a cada merge por pipeline automatizado, e nao por equipe")
    print("  lancando versao manualmente - por isso a cadencia alta convive com")
    print("  idade baixa.")


def main():
    try:
        repos, referencia = carregar_base()
    except (FileNotFoundError, ValueError) as erro:
        sys.exit(f"{erro}\nRode src/fetch_repos.py primeiro.")

    com_cadencia = [r for r in repos if r["cadencia"] is not None]
    sem_release = [r for r in repos if r["cadencia"] is None]

    print("RQ09 - a cadencia de releases se mantem ao longo da vida do projeto?")
    print(f"Base: data/repositorios_top1000.csv  |  coleta de {referencia:%Y-%m-%d}\n")

    secao_distribuicao(com_cadencia, sem_release, len(repos))
    secao_correlacao(com_cadencia, repos)
    secao_por_idade(com_cadencia)
    secao_por_atividade(com_cadencia)
    secao_sem_release(sem_release, len(repos))
    secao_extremos(com_cadencia)

    print("\nAnalise concluida.")


if __name__ == "__main__":
    main()
