"""
Lab01S01 - Validacao rapida da extracao (RQ03, RQ04).

RQ03 - Sistemas populares lancam releases com frequencia?
       Metrica: total de releases (coluna total_releases).
RQ04 - Sistemas populares sao atualizados com frequencia?
       Metrica: tempo ate a ultima atualizacao (colunas ultima_atualizacao e
       dias_desde_ultima_atualizacao), com ultimo_push e dias_desde_ultimo_push
       como leitura complementar.

Sobre a RQ04: o updatedAt do GitHub sobe a cada estrela ou watch recebido, e nao
so quando o codigo muda. Nos 100 repositorios mais populares ele deu 0 dia para
todos, porque eles ganham estrelas o tempo inteiro. Por isso esta validacao
acompanha as duas colunas: o pushedAt e o unico dos dois que distingue um
repositorio ativo de um abandonado.

Uso:
    python src/fetch_repos.py                    # gera o CSV primeiro
    python src/validate_sample_rq03_rq04.py      # valida uma amostra de 8 repos
    python src/validate_sample_rq03_rq04.py 5    # valida uma amostra de 5 repos
"""

import csv
import statistics
import sys
from datetime import datetime, timezone

DEFAULT_SAMPLE_SIZE = 8
CSV_PATH = "data/repositorios_top100.csv"
TOLERANCIA_DIAS = 1


def load_sample(path, sample_size):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return rows[:sample_size]


def validate_data(row, coluna_data, coluna_dias, agora):
    problems = []

    try:
        data = datetime.strptime(row[coluna_data], "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return [f"{coluna_data} fora do formato ISO esperado"]

    data = data.replace(tzinfo=timezone.utc)
    if data > agora:
        problems.append(f"{coluna_data} no futuro")

    dias = int(row[coluna_dias])
    if dias < 0:
        problems.append(f"{coluna_dias} negativo")

    # A coluna derivada foi calculada na hora da coleta, entao ela so pode ser
    # menor ou igual ao recalculo de agora. Se for maior, a data bruta e a
    # coluna derivada nao vieram do mesmo repositorio.
    esperado = (agora - data).days
    if dias > esperado + TOLERANCIA_DIAS:
        problems.append(
            f"{coluna_dias} ({dias}) incompativel com "
            f"{coluna_data} (esperado no maximo {esperado})"
        )

    return problems


def validate_row(row, agora):
    problems = []

    releases = int(row["total_releases"])
    if releases < 0:
        problems.append("total_releases negativo")
    elif releases == 0:
        problems.append("aviso: repositorio sem nenhuma release")

    problems += validate_data(row, "ultima_atualizacao", "dias_desde_ultima_atualizacao", agora)
    problems += validate_data(row, "ultimo_push", "dias_desde_ultimo_push", agora)

    # Nao comparamos ultimo_push com ultima_atualizacao: um push em branch que
    # nao a default sobe o pushedAt sem subir o updatedAt, entao o push ficar
    # alguns minutos a frente e comportamento normal da API, nao erro de coleta.

    return problems


def main():
    sample_size = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SAMPLE_SIZE

    try:
        sample = load_sample(CSV_PATH, sample_size)
    except FileNotFoundError:
        sys.exit(f"Arquivo {CSV_PATH} nao encontrado. Rode src/fetch_repos.py primeiro.")

    if not sample:
        sys.exit(f"Arquivo {CSV_PATH} esta vazio.")

    agora = datetime.now(timezone.utc)
    print(f"Validando amostra de {len(sample)} repositorios de {CSV_PATH}\n")

    for row in sample:
        problems = validate_row(row, agora)
        status = "OK" if not problems else "ATENCAO"
        print(
            f"[{status}] {row['repositorio']} "
            f"(releases={row['total_releases']}, "
            f"dias_sem_atualizar={row['dias_desde_ultima_atualizacao']}, "
            f"dias_sem_push={row['dias_desde_ultimo_push']})"
        )
        for problem in problems:
            print(f"    - {problem}")

    releases = [int(row["total_releases"]) for row in sample]
    dias_update = [int(row["dias_desde_ultima_atualizacao"]) for row in sample]
    dias_push = [int(row["dias_desde_ultimo_push"]) for row in sample]

    print(f"\nRQ03 - mediana de releases na amostra: {statistics.median(releases)}")
    print(f"RQ04 - mediana de dias sem atualizacao (updatedAt): {statistics.median(dias_update)}")
    print(f"RQ04 - mediana de dias sem push (pushedAt): {statistics.median(dias_push)}")
    print("\nValidacao concluida.")


if __name__ == "__main__":
    main()
