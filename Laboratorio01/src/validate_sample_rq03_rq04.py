"""
Lab01S02 - Validacao de consistencia das RQ03 e RQ04 nos 1000 repositorios.

RQ03 - Sistemas populares lancam releases com frequencia?
       Metrica: total de releases (coluna total_releases).
RQ04 - Sistemas populares sao atualizados com frequencia?
       Metrica: tempo ate a ultima atualizacao (colunas ultima_atualizacao e
       dias_desde_ultima_atualizacao), com ultimo_push e dias_desde_ultimo_push
       como leitura complementar.

Na S01 esta validacao rodava sobre uma amostra de 8 repositorios e checava
apenas o formato de cada campo. Na S02, com a paginacao entregue, ela passa a
rodar sobre os 1000 repositorios e a olhar distribuicao, outliers e valores
ausentes, que e o que o enunciado pede desta sprint.

Sobre a RQ04: o updatedAt do GitHub sobe a cada estrela ou watch recebido, e nao
so quando o codigo muda. Nos 1000 repositorios mais populares ele fica saturado
perto de zero, porque eles ganham estrelas o tempo inteiro. Por isso esta
validacao acompanha as duas colunas: o pushedAt e o unico dos dois que distingue
um repositorio ativo de um abandonado.

Uso:
    python src/fetch_repos.py                    # gera o CSV primeiro
    python src/validate_sample_rq03_rq04.py      # valida os 1000 repositorios (S02)
    python src/validate_sample_rq03_rq04.py 8    # valida so uma amostra de 8 (S01)
"""

import csv
import statistics
import sys
from datetime import datetime, timezone

DEFAULT_SAMPLE_SIZE = None  # None = todos os repositorios do CSV (validacao S02)
CSV_PATH = "data/repositorios_top1000.csv"
TOLERANCIA_DIAS = 1

# Teto do campo releases.totalCount na API do GitHub. Se muitos repositorios
# encostarem nele, a metrica da RQ03 esta truncada e nao real.
TETO_RELEASES = 1000

# Faixas usadas para descrever a distribuicao da RQ04. O corte de 365 dias
# separa o que ainda recebe manutencao do que esta parado ha mais de um ano.
# A primeira faixa e aberta embaixo (minimo None) para nao deixar de fora o
# valor negativo gerado por push durante a coleta.
FAIXAS_DIAS = [
    ("ate 7 dias", None, 7),
    ("8 a 30 dias", 8, 30),
    ("31 a 90 dias", 31, 90),
    ("91 a 365 dias", 91, 365),
    ("mais de 365 dias", 366, None),
]


def load_sample(path, sample_size):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return rows[:sample_size] if sample_size else rows


def validate_data(row, coluna_data, coluna_dias, agora):
    """Checagens estruturais de um par (data bruta, dias derivados)."""
    erros = []
    avisos = []

    try:
        data = datetime.strptime(row[coluna_data], "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return [f"{coluna_data} fora do formato ISO esperado"], avisos

    data = data.replace(tzinfo=timezone.utc)
    if data > agora:
        erros.append(f"{coluna_data} no futuro")

    dias = int(row[coluna_dias])
    if dias < 0:
        # Um push feito depois do inicio da coleta e antes da leitura daquela
        # pagina deixa a diferenca negativa por questao de minutos. E artefato
        # de coleta, nao dado invalido, entao entra como aviso.
        avisos.append(f"{coluna_dias} negativo ({dias}) - push durante a coleta")

    # A coluna derivada foi calculada na hora da coleta, entao ela so pode ser
    # menor ou igual ao recalculo de agora. Se for maior, a data bruta e a
    # coluna derivada nao vieram do mesmo repositorio.
    esperado = (agora - data).days
    if dias > esperado + TOLERANCIA_DIAS:
        erros.append(
            f"{coluna_dias} ({dias}) incompativel com "
            f"{coluna_data} (esperado no maximo {esperado})"
        )

    return erros, avisos


def validate_row(row, agora):
    erros = []
    avisos = []

    releases = int(row["total_releases"])
    if releases < 0:
        erros.append("total_releases negativo")
    elif releases == 0:
        avisos.append("repositorio sem nenhuma release")

    for coluna_data, coluna_dias in (
        ("ultima_atualizacao", "dias_desde_ultima_atualizacao"),
        ("ultimo_push", "dias_desde_ultimo_push"),
    ):
        erros_data, avisos_data = validate_data(row, coluna_data, coluna_dias, agora)
        erros += erros_data
        avisos += avisos_data

    # Nao comparamos ultimo_push com ultima_atualizacao: um push em branch que
    # nao a default sobe o pushedAt sem subir o updatedAt, entao o push ficar
    # alguns minutos a frente e comportamento normal da API, nao erro de coleta.

    return erros, avisos


def validar_linha_a_linha(sample, agora):
    print(f"=== Validacao estrutural campo a campo ({len(sample)} repositorios) ===")

    com_erro = 0
    avisos_por_tipo = {}

    for row in sample:
        erros, avisos = validate_row(row, agora)
        if erros:
            com_erro += 1
            print(f"[ATENCAO] {row['repositorio']}")
            for erro in erros:
                print(f"    - {erro}")
        for aviso in avisos:
            chave = aviso.split(" (")[0]
            avisos_por_tipo.setdefault(chave, []).append(row["repositorio"])

    if not com_erro:
        print("  nenhuma inconsistencia estrutural encontrada.")
    print(f"  repositorios com inconsistencia .............: {com_erro}/{len(sample)}")

    for chave, repos in sorted(avisos_por_tipo.items()):
        exemplo = f" (ex.: {repos[0]})" if len(repos) <= 3 else ""
        print(f"  aviso -- {chave}: {len(repos)}{exemplo}")


def resumo_numerico(valores):
    """Mediana, media e quartis de uma lista, no formato usado nos prints."""
    if len(valores) < 4:
        return (
            f"mediana={statistics.median(valores):.0f}  "
            f"media={statistics.mean(valores):.1f}  "
            f"min={min(valores)}  max={max(valores)}"
        )

    q1, _, q3 = statistics.quantiles(valores, n=4)
    return (
        f"mediana={statistics.median(valores):.0f}  "
        f"media={statistics.mean(valores):.1f}  "
        f"Q1={q1:.0f}  Q3={q3:.0f}  "
        f"min={min(valores)}  max={max(valores)}"
    )


def validar_distribuicao_rq03(sample):
    total = len(sample)
    ausentes = sum(1 for r in sample if r["total_releases"] == "")
    releases = [int(r["total_releases"]) for r in sample if r["total_releases"] != ""]

    print("\n=== RQ03 - total de releases ===")
    print(f"  valores ausentes (total_releases vazio) ....: {ausentes} ({ausentes / total * 100:.1f}%)")
    if not releases:
        print("  nenhum valor de releases valido encontrado.")
        return

    print(f"  {resumo_numerico(releases)}")

    sem_release = sum(1 for v in releases if v == 0)
    ate_10 = sum(1 for v in releases if 0 < v <= 10)
    acima_100 = sum(1 for v in releases if v > 100)
    print(f"  outliers -- nenhuma release ................: {sem_release} ({sem_release / len(releases) * 100:.1f}%)")
    print(f"  entre 1 e 10 releases ......................: {ate_10} ({ate_10 / len(releases) * 100:.1f}%)")
    print(f"  acima de 100 releases ......................: {acima_100} ({acima_100 / len(releases) * 100:.1f}%)")

    no_teto = [
        r["repositorio"] for r in sample
        if r["total_releases"] != "" and int(r["total_releases"]) >= TETO_RELEASES
    ]
    if no_teto:
        print(f"  ATENCAO -- no teto de {TETO_RELEASES} releases ..........: {len(no_teto)} (ex.: {no_teto[0]})")
        print("             valor truncado pela API, tratar como limite inferior.")

    print("  top 5 repositorios por total de releases:")
    for row in sorted((r for r in sample if r["total_releases"] != ""),
                      key=lambda r: -int(r["total_releases"]))[:5]:
        print(f"    {row['repositorio']:45s} {row['total_releases']:>6s} releases")


def distribuicao_por_faixa(valores):
    linhas = []
    for rotulo, minimo, maximo in FAIXAS_DIAS:
        if minimo is None:
            qtd = sum(1 for v in valores if v <= maximo)
        elif maximo is None:
            qtd = sum(1 for v in valores if v >= minimo)
        else:
            qtd = sum(1 for v in valores if minimo <= v <= maximo)
        linhas.append((rotulo, qtd, qtd / len(valores) * 100))
    return linhas


def validar_distribuicao_rq04(sample):
    total = len(sample)

    print("\n=== RQ04 - tempo ate a ultima atualizacao ===")

    for coluna, rotulo in (
        ("dias_desde_ultima_atualizacao", "updatedAt (leitura literal do enunciado)"),
        ("dias_desde_ultimo_push", "pushedAt (leitura complementar)"),
    ):
        ausentes = sum(1 for r in sample if r[coluna] == "")
        valores = [int(r[coluna]) for r in sample if r[coluna] != ""]

        print(f"\n  -- {rotulo}")
        print(f"  valores ausentes ({coluna}): {ausentes} ({ausentes / total * 100:.1f}%)")
        if not valores:
            print("  nenhum valor valido encontrado.")
            continue

        print(f"  {resumo_numerico(valores)}")
        for rot, qtd, pct in distribuicao_por_faixa(valores):
            print(f"    {rot:20s} {qtd:4d} ({pct:5.1f}%)")

        zeros = sum(1 for v in valores if v <= 0)
        print(f"  outliers -- 0 dia ou menos .................: {zeros} ({zeros / len(valores) * 100:.1f}%)")

    # A comparacao entre as duas colunas e o resultado central desta validacao:
    # se o updatedAt estiver saturado em zero, ele nao responde a RQ04 e a
    # analise da S03 precisa usar o pushedAt.
    update = [int(r["dias_desde_ultima_atualizacao"]) for r in sample if r["dias_desde_ultima_atualizacao"] != ""]
    push = [int(r["dias_desde_ultimo_push"]) for r in sample if r["dias_desde_ultimo_push"] != ""]

    if update and push:
        saturados = sum(1 for v in update if v == 0)
        print("\n  comparacao das duas colunas:")
        print(f"    repositorios com updatedAt = 0 dia ......: {saturados} ({saturados / len(update) * 100:.1f}%)")
        print(f"    amplitude do updatedAt ..................: {min(update)} a {max(update)} dias")
        print(f"    amplitude do pushedAt ...................: {min(push)} a {max(push)} dias")
        if saturados / len(update) > 0.5:
            print("    conclusao: updatedAt saturado, sem poder de discriminacao;")
            print("               usar pushedAt como metrica efetiva da RQ04.")

    print("\n  top 5 repositorios mais tempo sem push:")
    for row in sorted((r for r in sample if r["dias_desde_ultimo_push"] != ""),
                      key=lambda r: -int(r["dias_desde_ultimo_push"]))[:5]:
        print(f"    {row['repositorio']:45s} {row['dias_desde_ultimo_push']:>5s} dias")


def main():
    sample_size = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SAMPLE_SIZE

    try:
        sample = load_sample(CSV_PATH, sample_size)
    except FileNotFoundError:
        sys.exit(f"Arquivo {CSV_PATH} nao encontrado. Rode src/fetch_repos.py primeiro.")

    if not sample:
        sys.exit(f"Arquivo {CSV_PATH} esta vazio.")

    agora = datetime.now(timezone.utc)
    print(f"Validando {len(sample)} repositorios de {CSV_PATH}\n")

    validar_linha_a_linha(sample, agora)
    validar_distribuicao_rq03(sample)
    validar_distribuicao_rq04(sample)

    print("\nValidacao concluida.")


if __name__ == "__main__":
    main()
