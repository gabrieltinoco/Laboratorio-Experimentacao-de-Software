"""
Snapshot de fechamento de sprint - GitHub Projects (v2).

Ao final de cada sprint (Lab01S01, S02, S03...), exporta os itens do Project
do grupo e o status atual de cada um (coluna do board) para um CSV. As
execucoes se acumulam no mesmo arquivo (uma linha por item por sprint), para
servir de base de dados historica aos Labs 04 e 05.

Uso:
    1. O token em .env precisa do escopo read:project (classic PAT) ou do
       escopo Projects (fine-grained), alem de acesso de leitura ao repo -
       diferente da consulta da Parte 1, a API de Projects exige esse escopo
       mesmo para board publico.
    2. Rode: python src/export_project_snapshot.py --sprint Lab01S01
"""

import argparse
import csv
import os
import sys
from datetime import datetime, timezone

import requests

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"

PROJECT_OWNER = "gabrieltinoco"
PROJECT_NUMBER = 2
PAGE_SIZE = 50


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
query ProjectItems($login: String!, $number: Int!, $perPage: Int!, $after: String) {
  user(login: $login) {
    projectV2(number: $number) {
      items(first: $perPage, after: $after) {
        pageInfo {
          hasNextPage
          endCursor
        }
        nodes {
          id
          status: fieldValueByName(name: "Status") {
            ... on ProjectV2ItemFieldSingleSelectValue {
              name
            }
          }
          content {
            __typename
            ... on Issue {
              number
              title
              state
              url
              assignees(first: 5) {
                nodes {
                  login
                }
              }
            }
            ... on PullRequest {
              number
              title
              state
              url
              assignees(first: 5) {
                nodes {
                  login
                }
              }
            }
            ... on DraftIssue {
              title
            }
          }
        }
      }
    }
  }
}
"""


def run_query(after=None):
    if not TOKEN:
        sys.exit("Defina a variavel de ambiente GITHUB_TOKEN antes de rodar o script.")

    headers = {"Authorization": f"Bearer {TOKEN}"}
    variables = {
        "login": PROJECT_OWNER,
        "number": PROJECT_NUMBER,
        "perPage": PAGE_SIZE,
        "after": after,
    }

    response = requests.post(
        GITHUB_GRAPHQL_URL,
        json={"query": QUERY, "variables": variables},
        headers=headers,
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()

    if "errors" in payload:
        sys.exit(f"Erro na consulta GraphQL: {payload['errors']}")

    return payload["data"]["user"]["projectV2"]["items"]


def fetch_all_items():
    items = []
    after = None

    while True:
        result = run_query(after)
        items.extend(result["nodes"])

        if not result["pageInfo"]["hasNextPage"]:
            break
        after = result["pageInfo"]["endCursor"]

    return items


def extract_row(item, sprint, snapshot_date):
    content = item["content"]
    content_type = content["__typename"] if content else "SemConteudo"
    assignees = content.get("assignees", {}).get("nodes", []) if content else []

    return {
        "sprint": sprint,
        "data_snapshot": snapshot_date,
        "item_id": item["id"],
        "tipo": content_type,
        "issue_numero": content.get("number", "") if content else "",
        "titulo": content.get("title", "") if content else "",
        "status_board": item["status"]["name"] if item["status"] else "",
        "estado_issue": content.get("state", "") if content else "",
        "responsaveis": ";".join(a["login"] for a in assignees),
        "url": content.get("url", "") if content else "",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sprint",
        required=True,
        help="Identificador da sprint (ex.: Lab01S01, Lab01S02)",
    )
    parser.add_argument(
        "--output",
        default=os.path.join("data", "project_snapshots.csv"),
        help="Arquivo CSV acumulado de snapshots (default: data/project_snapshots.csv)",
    )
    args = parser.parse_args()

    items = fetch_all_items()
    snapshot_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows = [extract_row(item, args.sprint, snapshot_date) for item in items]

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    file_exists = os.path.exists(args.output)

    with open(args.output, "a", newline="", encoding="utf-8") as f:
        fieldnames = rows[0].keys() if rows else [
            "sprint", "data_snapshot", "item_id", "tipo", "issue_numero",
            "titulo", "status_board", "estado_issue", "responsaveis", "url",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)

    print(f"{len(rows)} itens do sprint '{args.sprint}' adicionados a {args.output}")


if __name__ == "__main__":
    main()
