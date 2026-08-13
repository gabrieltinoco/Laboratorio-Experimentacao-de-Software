from __future__ import annotations

import csv
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

# --------------------------------------------------------------------------- #
# Se o script nao achar as colunas automaticamente, adicione o nome exato
# que aparece no seu CSV numa destas listas.
# --------------------------------------------------------------------------- #
COLUNAS_DATA_CRIACAO = ["created_at", "createdAt", "data_criacao", "criado_em"]
COLUNAS_PR_ACEITAS = [
    "merged_pull_requests", "pull_requests_aceitas", "pull_requests_merged",
    "prs_aceitas", "mergedPullRequests",
]
COLUNAS_NOME_REPO = ["name_with_owner", "nameWithOwner", "nome", "repositorio", "full_name"]


def localizar_csv(argv: list[str]) -> Path:
    if argv:
        caminho = Path(argv[0])
        if caminho.exists():
            return caminho
        raise SystemExit(f"Arquivo nao encontrado: {caminho}")

    raiz_projeto = Path(__file__).resolve().parent.parent  # sobe de src/ para a raiz
    candidatos = [
        raiz_projeto / "data" / "repositorios_top100.csv",
        raiz_projeto / "data" / "repositorios_top100" / "repositorios_top100.csv",
        raiz_projeto / "data" / "processed" / "repositories.csv",
    ]
    for candidato in candidatos:
        if candidato.exists():
            return candidato

    raise SystemExit(
        "Nao encontrei o CSV automaticamente. Rode assim:\n"
        "    python rq01_rq02.py caminho/para/seu.csv"
    )


def escolher_coluna (cabecalho: list[str], opcoes: list[str], rotulo: str):
    for opcao in opcoes:
        if opcao in cabecalho:
            return opcao
    raise SystemExit(
        f"Nao encontrei a coluna de '{rotulo}' no CSV.\n"
        f"Colunas disponiveis: {cabecalho}\n"
        f"Adicione o nome certo na lista COLUNAS_* no topo do script."
    )


def parse_data(valor: str) -> datetime | None:
    if not valor:
        return None
    valor = valor.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(valor)
    except ValueError:
        for formato in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(valor, formato)
            except ValueError:
                continue
    return None


def main() -> int:
    caminho_csv = localizar_csv(sys.argv[1:])
    agora = datetime.now(timezone.utc)

    with caminho_csv.open(encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.DictReader(arquivo)
        cabecalho = leitor.fieldnames or []
        col_data = escolher_coluna(cabecalho, COLUNAS_DATA_CRIACAO, "data de criacao (RQ01)")
        col_prs = escolher_coluna(cabecalho, COLUNAS_PR_ACEITAS, "pull requests aceitas (RQ02)")
        col_nome = next((c for c in COLUNAS_NOME_REPO if c in cabecalho), None)

        idades_anos: list[float] = []
        prs_aceitas: list[int] = []
        linhas_com_problema = 0

        for i, linha in enumerate(leitor, start=1):
            nome = linha.get(col_nome, f"linha {i}") if col_nome else f"linha {i}"

            data_criacao = parse_data(linha.get(col_data, ""))
            if data_criacao is None:
                linhas_com_problema += 1
                print(f"  [aviso] {nome}: data de criacao invalida/vazia, RQ01 ignorado")
            else:
                idades_anos.append((agora - data_criacao).days / 365.25)

            try:
                prs_aceitas.append(int(float(linha.get(col_prs, "0"))))
            except (ValueError, TypeError):
                linhas_com_problema += 1
                print(f"  [aviso] {nome}: pull requests aceitas invalido/vazio, RQ02 ignorado")

    print()
    print(f"Arquivo lido: {caminho_csv}")
    print(f"Coluna de data de criacao usada: {col_data}")
    print(f"Coluna de pull requests aceitas usada: {col_prs}")
    print(f"Linhas com problema (ignoradas na respectiva metrica): {linhas_com_problema}")
    print()

    print("=== RQ01 - Sistemas populares sao maduros/antigos? ===")
    if idades_anos:
        print(f"  n = {len(idades_anos)}")
        print(f"  idade mediana .......: {statistics.median(idades_anos):.2f} anos")
        print(f"  idade media .........: {statistics.mean(idades_anos):.2f} anos")
        print(f"  mais novo ...........: {min(idades_anos):.2f} anos")
        print(f"  mais antigo .........: {max(idades_anos):.2f} anos")
        acima_5 = sum(1 for i in idades_anos if i >= 5) / len(idades_anos)
        print(f"  % com 5 anos ou mais: {acima_5 * 100:.1f}%")
    else:
        print("  Nenhum valor de data valido encontrado.")
    print()

    print("=== RQ02 - Recebem muita contribuicao externa? ===")
    if prs_aceitas:
        print(f"  n = {len(prs_aceitas)}")
        print(f"  mediana de PRs aceitas .: {statistics.median(prs_aceitas):.1f}")
        print(f"  media de PRs aceitas ...: {statistics.mean(prs_aceitas):.1f}")
        print(f"  minimo ..................: {min(prs_aceitas)}")
        print(f"  maximo ..................: {max(prs_aceitas)}")
        acima_500 = sum(1 for p in prs_aceitas if p >= 500) / len(prs_aceitas)
        print(f"  % com 500 ou mais PRs ...: {acima_500 * 100:.1f}%")
    else:
        print("  Nenhum valor de pull requests valido encontrado.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())