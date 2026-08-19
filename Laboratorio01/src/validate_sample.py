"""
RQ08: licenca SPDX de cada repositorio cruzada com estrelas e PRs aceitas,
 para checar se repositorios com licenca permissiva recebem mais
contribuicao externa que os sem licenca ou com licenca copyleft.

Uso:
    python src/fetch_repos.py          # gera o CSV primeiro
    python src/validate_sample.py      # valida os 1000 repositorios (S02)
    python src/validate_sample.py 8    # valida so uma amostra de 8 (S01)
"""

import csv
import statistics
import sys
from collections import Counter, defaultdict

DEFAULT_SAMPLE_SIZE = None  # None = todos os repositorios do CSV (validacao S02)
CSV_PATH = "data/repositorios_top1000.csv"
LINGUAGENS_POPULARES = ["TypeScript", "Python", "JavaScript", "Java", "C#"]  # GitHub Octoverse 2025

# RQ08 (bonus): classificacao de licencas SPDX em permissiva vs. copyleft,
# para comparar com repositorios sem licenca ou com licenca nao mapeada.
LICENCAS_PERMISSIVAS = {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "0BSD", "Unlicense"}
LICENCAS_COPYLEFT = {"GPL-2.0", "GPL-3.0", "LGPL-2.1", "LGPL-3.0", "AGPL-3.0", "MPL-2.0", "EPL-2.0"}


def load_sample(path, sample_size):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return rows[:sample_size] if sample_size else rows


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


def validar_linha_a_linha(sample):
    print(f"=== Validacao estrutural campo a campo ({len(sample)} repositorios) ===")
    linhas_com_problema = 0
    for row in sample:
        problems = [p for p in validate_row(row) if not p.startswith("aviso")]
        if problems:
            linhas_com_problema += 1
            print(f"[ATENCAO] {row['repositorio']}")
            for problem in problems:
                print(f"    - {problem}")
    if not linhas_com_problema:
        print("  nenhuma inconsistencia estrutural encontrada.")
    print(f"  repositorios com inconsistencia: {linhas_com_problema}/{len(sample)}")


def validar_distribuicao_rq05(sample):
    total = len(sample)
    contagem = Counter(row["linguagem_primaria"] for row in sample)
    sem_linguagem = contagem.get("Nao informada", 0)

    print(f"\n=== RQ05 - distribuicao de linguagens ({len(contagem)} distintas) ===")
    print(f"Fonte de 'linguagens populares': GitHub Octoverse 2025 (top 5: {', '.join(LINGUAGENS_POPULARES)})")
    for linguagem, qtd in contagem.most_common(10):
        marca = " *" if linguagem in LINGUAGENS_POPULARES else ""
        print(f"  {linguagem:20s} {qtd:4d} ({qtd / total * 100:5.1f}%){marca}")

    no_top5 = sum(qtd for ling, qtd in contagem.items() if ling in LINGUAGENS_POPULARES)
    cauda_longa = sum(1 for qtd in contagem.values() if qtd == 1)
    print(f"  valores ausentes (linguagem_primaria) ...: {sem_linguagem} ({sem_linguagem / total * 100:.1f}%)")
    print(f"  % em linguagem do top 5 Octoverse ........: {no_top5 / total * 100:.1f}%")
    print(f"  linguagens que aparecem em so 1 repo .....: {cauda_longa}")


def validar_outliers_rq06(sample):
    total = len(sample)
    percentuais = [float(r["percentual_issues_fechadas"]) for r in sample if r["percentual_issues_fechadas"]]
    ausentes = total - len(percentuais)

    print("\n=== RQ06 - percentual de issues fechadas ===")
    print(f"  valores ausentes (issues_total=0) ........: {ausentes} ({ausentes / total * 100:.1f}%)")
    if percentuais:
        zero = sum(1 for p in percentuais if p == 0)
        cem = sum(1 for p in percentuais if p == 1)
        print(f"  mediana ...................................: {statistics.median(percentuais) * 100:.1f}%")
        print(f"  minimo / maximo ...........................: {min(percentuais) * 100:.1f}% / {max(percentuais) * 100:.1f}%")
        print(f"  outliers -- 0% das issues fechadas ........: {zero}")
        print(f"  outliers -- 100% das issues fechadas ......: {cem}")


def validar_outliers_rq07(sample):
    total = len(sample)
    prs = [int(r["pull_requests_aceitas"]) for r in sample]
    releases = [int(r["total_releases"]) for r in sample]
    sem_releases = sum(1 for v in releases if v == 0)

    grupos = {
        "populares": {"prs": [], "releases": [], "dias": []},
        "outras": {"prs": [], "releases": [], "dias": []},
    }
    for r in sample:
        grupo = "populares" if r["linguagem_primaria"] in LINGUAGENS_POPULARES else "outras"
        grupos[grupo]["prs"].append(int(r["pull_requests_aceitas"]))
        grupos[grupo]["releases"].append(int(r["total_releases"]))
        grupos[grupo]["dias"].append(int(r["dias_desde_ultima_atualizacao"]))

    print("\n=== RQ07 - PRs aceitas e releases, por grupo de linguagem (RQ05) ===")
    for grupo, dados in grupos.items():
        print(
            f"  grupo '{grupo}' (n={len(dados['prs'])}): "
            f"mediana PRs={statistics.median(dados['prs']):.0f}, "
            f"mediana releases={statistics.median(dados['releases']):.0f}, "
            f"mediana dias sem atualizar={statistics.median(dados['dias']):.0f}"
        )
    print(f"  outlier -- maximo de PRs aceitas ..........: {max(prs)} ({sample[prs.index(max(prs))]['repositorio']})")
    print(f"  outlier -- maximo de releases ..............: {max(releases)} ({sample[releases.index(max(releases))]['repositorio']})")
    print(f"  repositorios sem nenhuma release ...........: {sem_releases} ({sem_releases / total * 100:.1f}%)")


def classificar_licenca(spdx):
    if not spdx or spdx == "Sem licenca":
        return "sem licenca"
    if spdx == "NOASSERTION":
        return "nao mapeada (NOASSERTION)"
    if spdx in LICENCAS_PERMISSIVAS:
        return "permissiva"
    if spdx in LICENCAS_COPYLEFT:
        return "copyleft"
    return "outra"


def validar_rq08_licenca(sample):
    print("\n=== RQ08 (bonus, fora do enunciado) - licenca x popularidade/contribuicao ===")

    if "licenca" not in sample[0]:
        print("  coluna 'licenca' nao encontrada no CSV -- rode src/fetch_repos.py de novo para atualizar os dados.")
        return

    total = len(sample)
    print("  Metrica: licenca SPDX (licenseInfo.spdxId) cruzada com estrelas e PRs aceitas (RQ02).")

    contagem = Counter(r["licenca"] for r in sample)
    for licenca, qtd in contagem.most_common(10):
        print(f"  {licenca:20s} {qtd:4d} ({qtd / total * 100:5.1f}%)")

    grupos = defaultdict(lambda: {"estrelas": [], "prs": []})
    for r in sample:
        grupo = classificar_licenca(r["licenca"])
        grupos[grupo]["estrelas"].append(int(r["estrelas"]))
        grupos[grupo]["prs"].append(int(r["pull_requests_aceitas"]))

    print("  grupos de licenca:")
    for grupo, dados in sorted(grupos.items(), key=lambda kv: -len(kv[1]["prs"])):
        print(
            f"    {grupo:24s} n={len(dados['prs']):4d}  "
            f"mediana estrelas={statistics.median(dados['estrelas']):.0f}  "
            f"mediana PRs aceitas={statistics.median(dados['prs']):.0f}"
        )

    sem_licenca = contagem.get("Sem licenca", 0)
    print(f"  repositorios sem licenca ...................: {sem_licenca} ({sem_licenca / total * 100:.1f}%)")


def main():
    sample_size = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SAMPLE_SIZE

    try:
        sample = load_sample(CSV_PATH, sample_size)
    except FileNotFoundError:
        sys.exit(f"Arquivo {CSV_PATH} nao encontrado. Rode src/fetch_repos.py primeiro.")

    print(f"Validando {len(sample)} repositorios de {CSV_PATH}\n")

    validar_linha_a_linha(sample)
    validar_distribuicao_rq05(sample)
    validar_outliers_rq06(sample)
    validar_outliers_rq07(sample)
    validar_rq08_licenca(sample)

    print("\nValidacao concluida.")


if __name__ == "__main__":
    main()
