"""
Lab01S01 - Mineracao de dados via GitHub GraphQL API.

Busca os 100 repositorios com mais estrelas no GitHub e salva os
campos necessarios para essas RQs em um CSV.

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

PAGE_SIZE = 10
TOTAL_REPOS = 100
MAX_RETRIES = 5


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
            time.sleep(2 * attempt)
            continue

        response.raise_for_status()
        payload = response.json()

        if "errors" in payload:
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
    output_path = os.path.join("data", "repositorios_top100.csv")

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"{len(rows)} repositorios salvos em {output_path}")


if __name__ == "__main__":
    main()