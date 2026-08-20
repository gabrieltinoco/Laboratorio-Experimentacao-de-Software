"""
Lab01S01/S02 - Mineracao de dados via GitHub GraphQL API.

Busca os 1000 repositorios com mais estrelas no GitHub, paginando a busca
por cursor, e salva num CSV todos os campos necessarios as RQs do
laboratorio. Na S01 a coleta ia ate 100 repositorios; a S02 ampliou o
alcance para 1000, que e tambem o teto de resultados que o endpoint
search devolve para uma mesma query.

Uso:
    1. Gere um Personal Access Token no GitHub (nao precisa de nenhum
       escopo, ja que os dados consultados sao publicos).
    2. Coloque o token num arquivo .env na raiz do projeto:
       GITHUB_TOKEN=ghp_seu_token_aqui
       (ou defina a variavel de ambiente GITHUB_TOKEN diretamente)
    3. Rode: python src/fetch_repos.py
"""

import csv
import os
import sys
import time
from datetime import datetime, timezone

import requests

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"

# Com 10 por pagina, coletar 1000 repositorios custava 100 requisicoes. Com 25
# cai para 40, o que reduz a exposicao ao limite de uso da API sem inflar o
# custo de cada requisicao: a query tem varias conexoes aninhadas (issues,
# pullRequests, releases), e paginas muito grandes aumentam a chance de a
# propria consulta estourar o tempo do lado do GitHub.
PAGE_SIZE = 25
TOTAL_REPOS = 1000
MAX_RETRIES = 5

# Espera entre tentativas depois de erro 5xx, multiplicada pelo numero da
# tentativa.
RETRY_WAIT_SECONDS = 2

# Espera usada quando o GitHub barra por limite de uso e nao informa em quanto
# tempo o limite volta.
RATE_LIMIT_WAIT_SECONDS = 60


def load_dotenv(path=".env"):
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


load_dotenv()
TOKEN = os.environ.get("GITHUB_TOKEN")

QUERY = """
query TopRepositories($queryString: String!, $perPage: Int!, $after: String) {
  search(query: $queryString, type: REPOSITORY, first: $perPage, after: $after) {
    repositoryCount
    pageInfo {
      hasNextPage
      endCursor
    }
    nodes {
      ... on Repository {
        nameWithOwner
        createdAt
        stargazerCount
        primaryLanguage {
          name
        }
        licenseInfo {
          spdxId
        }
        issues {
          totalCount
        }
        closedIssues: issues(states: CLOSED) {
          totalCount
        }
        mergedPullRequests: pullRequests(states: MERGED) {
          totalCount
        }
        releases {
          totalCount
        }
        updatedAt
        pushedAt
      }
    }
  }
}
"""


def espera_do_limite_de_uso(response, attempt):
    """Quantos segundos esperar quando o GitHub barra por limite de uso.

    O GitHub informa a espera de duas formas, e as duas sao respeitadas aqui:
    o cabecalho Retry-After (limite secundario, em segundos) e o par
    x-ratelimit-remaining / x-ratelimit-reset (limite primario, em epoch).
    Sem nenhum dos dois, cai numa espera fixa progressiva.
    """
    retry_after = response.headers.get("Retry-After", "")
    if retry_after.isdigit():
        return int(retry_after)

    reset = response.headers.get("x-ratelimit-reset", "")
    if response.headers.get("x-ratelimit-remaining") == "0" and reset.isdigit():
        return max(1, int(reset) - int(time.time()) + 1)

    return RATE_LIMIT_WAIT_SECONDS * attempt


def run_query(query_string, per_page, after=None):
    if not TOKEN:
        sys.exit("Defina a variavel de ambiente GITHUB_TOKEN antes de rodar o script.")

    headers = {"Authorization": f"Bearer {TOKEN}"}
    variables = {"queryString": query_string, "perPage": per_page, "after": after}

    for attempt in range(1, MAX_RETRIES + 1):
        response = requests.post(
            GITHUB_GRAPHQL_URL,
            json={"query": QUERY, "variables": variables},
            headers=headers,
            timeout=30,
        )

        if response.status_code >= 500 and attempt < MAX_RETRIES:
            print(f"  aviso: {response.status_code} do GitHub, tentando de novo...")
            time.sleep(RETRY_WAIT_SECONDS * attempt)
            continue

        # 403 e 429 sao como a API responde ao limite de uso. Sem este trecho,
        # uma coleta de 1000 repositorios que encosta no limite morre no meio e
        # tem de ser refeita do zero.
        if response.status_code in (403, 429) and attempt < MAX_RETRIES:
            espera = espera_do_limite_de_uso(response, attempt)
            print(f"  aviso: {response.status_code} (limite de uso), esperando {espera}s...")
            time.sleep(espera)
            continue

        response.raise_for_status()
        payload = response.json()

        if "errors" in payload:
            # O limite de uso do GraphQL tambem chega como erro dentro de uma
            # resposta 200, e nesse caso vale esperar e repetir em vez de
            # abortar. Qualquer outro erro e da consulta em si e nao melhora
            # com nova tentativa.
            tipos = {erro.get("type") for erro in payload["errors"]}
            if "RATE_LIMITED" in tipos and attempt < MAX_RETRIES:
                espera = RATE_LIMIT_WAIT_SECONDS * attempt
                print(f"  aviso: RATE_LIMITED no GraphQL, esperando {espera}s...")
                time.sleep(espera)
                continue

            sys.exit(f"Erro na consulta GraphQL: {payload['errors']}")

        return payload["data"]["search"]


def fetch_top_repos(total=TOTAL_REPOS, page_size=PAGE_SIZE):
    repos = []
    after = None

    while len(repos) < total:
        remaining = total - len(repos)
        result = run_query("stars:>1 sort:stars-desc", min(page_size, remaining), after)
        repos.extend(result["nodes"])
        print(f"  {len(repos)}/{total} repositorios buscados")

        if not result["pageInfo"]["hasNextPage"]:
            break
        after = result["pageInfo"]["endCursor"]

    return repos


# RQ04: a metrica pedida e o tempo ate a ultima atualizacao, entao guardamos
# tambem a diferenca em dias, e nao so o timestamp cru devolvido pela API.
#
# Coletamos updatedAt e pushedAt. O updatedAt e a leitura literal do enunciado,
# mas ele sobe a cada estrela ou watch recebido: nos 100 repositorios mais
# populares ele deu 0 dia para todos, o que nao responde a RQ04. O pushedAt so
# sobe quando ha push de codigo, entao e ele que separa um repositorio ativo de
# um parado. Os dois ficam no CSV para a analise poder comparar.
def dias_desde(timestamp):
    momento = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - momento).days


def extract_row(repo):
    total_issues = repo["issues"]["totalCount"]
    closed_issues = repo["closedIssues"]["totalCount"]

    return {
        "repositorio": repo["nameWithOwner"],
        "created_at": repo["createdAt"],
        "estrelas": repo["stargazerCount"],
        "linguagem_primaria": repo["primaryLanguage"]["name"] if repo["primaryLanguage"] else "Nao informada",
        # RQ08 (bonus, fora das RQs do enunciado): licenca SPDX, para cruzar
        # licenca permissiva/restritiva/sem licenca com popularidade e
        # contribuicao externa (RQ02).
        "licenca": repo["licenseInfo"]["spdxId"] if repo["licenseInfo"] else "Sem licenca",
        "issues_total": total_issues,
        "issues_fechadas": closed_issues,
        "percentual_issues_fechadas": round(closed_issues / total_issues, 4) if total_issues > 0 else "",
        "pull_requests_aceitas": repo["mergedPullRequests"]["totalCount"],
        "total_releases": repo["releases"]["totalCount"],
        "ultima_atualizacao": repo["updatedAt"],
        "dias_desde_ultima_atualizacao": dias_desde(repo["updatedAt"]),
        "ultimo_push": repo["pushedAt"],
        "dias_desde_ultimo_push": dias_desde(repo["pushedAt"]),
    }


def main():
    repos = fetch_top_repos()
    rows = [extract_row(repo) for repo in repos]

    os.makedirs("data", exist_ok=True)
    output_path = os.path.join("data", "repositorios_top1000.csv")

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"{len(rows)} repositorios salvos em {output_path}")


if __name__ == "__main__":
    main()