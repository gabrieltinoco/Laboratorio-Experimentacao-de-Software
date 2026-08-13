"""
Lab01S01 - Validacao rapida da extracao (RQ05, RQ06, RQ07).
Uso:
    python src/fetch_repos.py          # gera o CSV primeiro
    python src/validate_sample.py      # valida uma amostra de 8 repos
    python src/validate_sample.py 5    # valida uma amostra de 5 repos
"""

import csv
import sys

DEFAULT_SAMPLE_SIZE = 8
CSV_PATH = "data/repositorios_top100.csv"


def load_sample(path, sample_size):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return rows[:sample_size]


def validate_row(row):
    problems = []

    total = int(row["issues_total"])
    fechadas = int(row["issues_fechadas"])

    if fechadas > total:
        problems.append("issues_fechadas maior que issues_total")

    if row["percentual_issues_fechadas"]:
        percentual = float(row["percentual_issues_fechadas"])
        if not (0 <= percentual <= 1):
            problems.append("percentual_issues_fechadas fora do intervalo [0, 1]")

    if row["linguagem_primaria"] == "Nao informada":
        problems.append("aviso: repositorio sem linguagem primaria")

    if int(row["pull_requests_aceitas"]) < 0 or int(row["total_releases"]) < 0:
        problems.append("contagem negativa de pull requests ou releases")

    return problems


def main():
    sample_size = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SAMPLE_SIZE

    try:
        sample = load_sample(CSV_PATH, sample_size)
    except FileNotFoundError:
        sys.exit(f"Arquivo {CSV_PATH} nao encontrado. Rode src/fetch_repos.py primeiro.")

    print(f"Validando amostra de {len(sample)} repositorios de {CSV_PATH}\n")

    for row in sample:
        problems = validate_row(row)
        status = "OK" if not problems else "ATENCAO"
        print(
            f"[{status}] {row['repositorio']} "
            f"(linguagem={row['linguagem_primaria']}, "
            f"%issues_fechadas={row['percentual_issues_fechadas']})"
        )
        for problem in problems:
            print(f"    - {problem}")

    print("\nValidacao concluida.")


if __name__ == "__main__":
    main()
