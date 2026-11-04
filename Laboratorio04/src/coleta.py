"""Coleta dos dados reais: tempo ate o merge de PRs com e sem bot de revisao.

Uso (a partir da pasta Laboratorio04):

    $env:GITHUB_TOKEN = "ghp_..."      # Windows PowerShell
    export GITHUB_TOKEN=ghp_...        # Linux/macOS
    python -m src.coleta

O que o script faz:

1. Lista, pela API de busca, todos os PRs do repositorio com merge no periodo
   (`is:pr is:merged merged:INICIO..FIM`).
2. Descarta PRs abertos por bots (dependabot, Copilot coding agent etc.), porque
   o fluxo de merge deles e automatico e nao representa revisao humana.
3. Embaralha os PRs restantes com semente fixa e, nessa ordem, consulta
   `GET /repos/{owner}/{repo}/pulls/{n}/reviews` de cada um:
   - "com_bot": o PR tem ao menos uma review do bot de revisao (BOT_REVISAO);
   - "sem_bot": o PR nao tem nenhuma review do bot de revisao.
   Para assim que os dois grupos tiverem N_POR_GRUPO PRs.
4. Para os PRs sorteados, busca `GET /repos/{owner}/{repo}/pulls/{n}` para
   registrar o tamanho do PR (arquivos e linhas alteradas), usado so na
   discussao de limitacoes.
5. Calcula horas_ate_merge = merged_at - created_at e grava data/real/prs.csv.

O token e lido SOMENTE da variavel de ambiente GITHUB_TOKEN. As respostas da API
ficam em cache/ (fora do git), entao rodar de novo nao gasta cota e devolve o
mesmo CSV.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

# ---------------------------------------------------------------- parametros
REPOSITORIO = "microsoft/PowerToys"
BOT_REVISAO = "copilot-pull-request-reviewer[bot]"
INICIO = "2026-08-01"
FIM = "2026-10-31"
N_POR_GRUPO = 30
SEMENTE = 42

RAIZ = Path(__file__).resolve().parent.parent
DIR_CACHE = RAIZ / "cache"
ARQ_SAIDA = RAIZ / "data" / "real" / "prs.csv"
API = "https://api.github.com"


# ---------------------------------------------------------------- HTTP com cache
def _sessao() -> requests.Session:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("Defina a variavel de ambiente GITHUB_TOKEN antes de rodar a coleta.")
    s = requests.Session()
    s.headers.update(
        {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "lab04-teste-hipotese",
        }
    )
    return s


def _get(sessao: requests.Session, url: str, params: dict | None = None, pausa: float = 0.0):
    """GET com cache em disco e espera automatica no rate limit."""
    chave = hashlib.sha1(json.dumps([url, params], sort_keys=True).encode()).hexdigest()
    arq = DIR_CACHE / f"{chave}.json"
    if arq.exists():
        return json.loads(arq.read_text(encoding="utf-8"))

    for tentativa in range(6):
        r = sessao.get(url, params=params, timeout=30)
        if r.status_code == 200:
            dados = r.json()
            DIR_CACHE.mkdir(exist_ok=True)
            arq.write_text(json.dumps(dados), encoding="utf-8")
            time.sleep(pausa)
            return dados
        if r.status_code in (403, 429):
            reset = int(r.headers.get("x-ratelimit-reset", time.time() + 60))
            espera = max(reset - time.time(), 0) + 5 if r.headers.get("x-ratelimit-remaining") == "0" else 60
            print(f"  rate limit ({r.status_code}); aguardando {espera:.0f}s", flush=True)
            time.sleep(espera)
            continue
        if r.status_code >= 500:
            time.sleep(2**tentativa)
            continue
        r.raise_for_status()
    raise RuntimeError(f"Falha persistente em {url}")


# ---------------------------------------------------------------- etapas
def listar_prs_mergeados(sessao) -> list[dict]:
    """Todos os PRs com merge no periodo (API de busca, paginada)."""
    q = f"repo:{REPOSITORIO} is:pr is:merged merged:{INICIO}..{FIM}"
    itens, pagina = [], 1
    while True:
        d = _get(sessao, f"{API}/search/issues", {"q": q, "per_page": 100, "page": pagina}, pausa=2.5)
        if pagina == 1:
            total = d["total_count"]
            print(f"PRs com merge entre {INICIO} e {FIM}: {total}")
            if total > 1000:
                sys.exit("A busca devolve no maximo 1.000 resultados; reduza o periodo.")
        itens += d["items"]
        if len(itens) >= total or not d["items"]:
            return itens
        pagina += 1


def autor_e_bot(item: dict) -> bool:
    user = item["user"]
    return user.get("type") == "Bot" or user["login"].endswith("[bot]") or user["login"] == "Copilot"


def tem_review_do_bot(sessao, numero: int) -> bool:
    reviews, pagina = [], 1
    while True:
        lote = _get(sessao, f"{API}/repos/{REPOSITORIO}/pulls/{numero}/reviews", {"per_page": 100, "page": pagina})
        reviews += lote
        if len(lote) < 100:
            break
        pagina += 1
    return any((rv.get("user") or {}).get("login") == BOT_REVISAO for rv in reviews)


def coletar() -> pd.DataFrame:
    sessao = _sessao()
    itens = listar_prs_mergeados(sessao)
    # Ordena por numero antes de sortear: a ordem da busca nao e garantida.
    humanos = sorted((i for i in itens if not autor_e_bot(i)), key=lambda i: i["number"])
    print(f"Abertos por pessoas (sem bots como autor): {len(humanos)}")

    # Ordem aleatoria reprodutivel: o sorteio nao favorece PRs recentes ou antigos.
    rng = np.random.default_rng(SEMENTE)
    ordem = rng.permutation(len(humanos))

    grupos: dict[str, list[dict]] = {"com_bot": [], "sem_bot": []}
    avaliados = 0
    for idx in ordem:
        item = humanos[idx]
        avaliados += 1
        grupo = "com_bot" if tem_review_do_bot(sessao, item["number"]) else "sem_bot"
        if len(grupos[grupo]) < N_POR_GRUPO:
            grupos[grupo].append(item)
        if all(len(g) == N_POR_GRUPO for g in grupos.values()):
            break
    print(f"PRs avaliados ate fechar {N_POR_GRUPO} por grupo: {avaliados}")
    for g, lst in grupos.items():
        if len(lst) < N_POR_GRUPO:
            print(f"AVISO: grupo {g} ficou com {len(lst)} PRs (menos que {N_POR_GRUPO}).")

    linhas = []
    for grupo, lst in grupos.items():
        for item in lst:
            pr = _get(sessao, f"{API}/repos/{REPOSITORIO}/pulls/{item['number']}")
            criado = pd.Timestamp(pr["created_at"])
            mergeado = pd.Timestamp(pr["merged_at"])
            linhas.append(
                {
                    "numero": pr["number"],
                    "grupo": grupo,
                    "created_at": pr["created_at"],
                    "merged_at": pr["merged_at"],
                    "horas_ate_merge": round((mergeado - criado).total_seconds() / 3600, 4),
                    "url": pr["html_url"],
                    "autor": pr["user"]["login"],
                    "arquivos_alterados": pr["changed_files"],
                    "linhas_alteradas": pr["additions"] + pr["deletions"],
                }
            )
    df = pd.DataFrame(linhas).sort_values(["grupo", "numero"]).reset_index(drop=True)
    return df


def main() -> None:
    df = coletar()
    ARQ_SAIDA.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(ARQ_SAIDA, index=False)
    print(f"\nGravado {ARQ_SAIDA.relative_to(RAIZ)} ({len(df)} linhas)")
    print(df.groupby("grupo")["horas_ate_merge"].describe().round(2).to_string())


if __name__ == "__main__":
    main()
