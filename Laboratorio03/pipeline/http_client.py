"""Cliente HTTP da API REST do GitHub, escrito pelo grupo (Issue #2).

O enunciado proibe bibliotecas prontas de acesso a API (PyGithub etc.), entao
este modulo faz as requisicoes direto com `requests` e cuida de:

- autenticacao com o token lido de GITHUB_TOKEN (nunca gravado em disco);
- paginacao seguindo o header `Link` (rel="next");
- cache em disco, um JSON por requisicao, organizado por repositorio. Rodar a
  coleta de novo depois de uma interrupcao reaproveita tudo que ja foi salvo;
- espera automatica quando a cota acaba (X-RateLimit-Remaining / Reset, com
  consulta a /rate_limit quando os headers nao vierem);
- backoff exponencial (1, 2, 4, 8 s...) para respostas 5xx e erros de rede.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterator
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import requests

log = logging.getLogger(__name__)

API_URL = "https://api.github.com"

# Erros 4xx estaveis: a resposta nao muda se repetirmos a chamada, entao vale
# guardar no cache para a retomada nao gastar cota com eles de novo.
# 404: tag apagada no compare, repo removido; 409: repositorio vazio;
# 451: bloqueado por motivo legal; 422: compare entre historias sem relacao.
STATUS_CACHEAVEIS_DE_ERRO = {404, 409, 422, 451}

_LINK_RE = re.compile(r'<([^>]+)>\s*;\s*rel="([^"]+)"')


class ErroGitHub(Exception):
    """Resposta de erro que nao sera repetida (4xx ou tentativas esgotadas)."""

    def __init__(self, status: int, url: str, mensagem: str = ""):
        self.status = status
        self.url = url
        super().__init__(f"HTTP {status} em {url}" + (f": {mensagem}" if mensagem else ""))


@dataclass
class Resposta:
    """O que o cliente devolve (e o que fica salvo no cache)."""

    status: int
    url: str
    dados: Any
    links: dict[str, str] = field(default_factory=dict)
    do_cache: bool = False


def parse_link(header: str | None) -> dict[str, str]:
    """Converte o header `Link` em {rel: url}, ex.: {"next": ..., "last": ...}."""
    if not header:
        return {}
    return {rel: url for url, rel in _LINK_RE.findall(header)}


def numero_da_pagina(url: str) -> int | None:
    """Le o parametro `page` de uma URL (usado com o rel="last")."""
    for chave, valor in parse_qsl(urlsplit(url).query):
        if chave == "page":
            return int(valor)
    return None


def montar_url(base_url: str, caminho: str, params: dict | None = None) -> str:
    """URL absoluta e canonica (params ordenados), usada tambem como chave do cache."""
    url = caminho if caminho.startswith("http") else base_url.rstrip("/") + "/" + caminho.lstrip("/")
    partes = urlsplit(url)
    query = dict(parse_qsl(partes.query))
    if params:
        query.update({k: str(v) for k, v in params.items() if v is not None})
    return urlunsplit((partes.scheme, partes.netloc, partes.path, urlencode(sorted(query.items())), ""))


class Cache:
    """Um JSON por requisicao: <raiz>/<owner__repo ou endpoint>/<sha1 da URL>.json.

    A escrita e atomica (arquivo temporario + os.replace): um Ctrl+C no meio da
    gravacao nunca deixa um JSON corrompido para a proxima execucao.
    """

    def __init__(self, raiz: str | Path):
        self.raiz = Path(raiz)

    def caminho(self, url: str) -> Path:
        segmentos = [s for s in urlsplit(url).path.split("/") if s]
        if len(segmentos) >= 3 and segmentos[0] == "repos":
            pasta = Path("repos") / f"{segmentos[1]}__{segmentos[2]}"
        else:
            pasta = Path(segmentos[0] if segmentos else "_raiz")
        chave = hashlib.sha1(url.encode("utf-8")).hexdigest()
        return self.raiz / pasta / f"{chave}.json"

    def ler(self, url: str) -> Resposta | None:
        arquivo = self.caminho(url)
        if not arquivo.exists():
            return None
        try:
            bruto = json.loads(arquivo.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            log.warning("Cache ilegivel, refazendo a chamada: %s", arquivo)
            return None
        return Resposta(bruto["status"], bruto["url"], bruto["dados"], bruto.get("links", {}), do_cache=True)

    def gravar(self, resposta: Resposta) -> None:
        arquivo = self.caminho(resposta.url)
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        temporario = arquivo.with_suffix(".tmp")
        conteudo = {"status": resposta.status, "url": resposta.url, "dados": resposta.dados, "links": resposta.links}
        temporario.write_text(json.dumps(conteudo, ensure_ascii=False), encoding="utf-8")
        os.replace(temporario, arquivo)


class GitHubClient:
    def __init__(
        self,
        token: str | None = None,
        cache_dir: str | Path = "cache",
        base_url: str = API_URL,
        per_page: int = 100,
        max_tentativas: int = 5,
        backoff_base_s: float = 1.0,
        timeout_s: float = 30.0,
        sessao: requests.Session | None = None,
        dormir: Callable[[float], None] = time.sleep,
        agora: Callable[[], float] = time.time,
    ):
        self.token = token if token is not None else os.environ.get("GITHUB_TOKEN")
        if not self.token:
            log.warning("GITHUB_TOKEN nao definido: a API limita a 60 requisicoes por hora.")
        self.cache = Cache(cache_dir)
        self.base_url = base_url
        self.per_page = per_page
        self.max_tentativas = max_tentativas
        self.backoff_base_s = backoff_base_s
        self.timeout_s = timeout_s
        self.sessao = sessao or requests.Session()
        self.dormir = dormir
        self.agora = agora
        self.chamadas_rede = 0  # requisicoes que de fato foram a API (inclui /rate_limit)

    @classmethod
    def from_config(cls, config: dict, **kwargs) -> "GitHubClient":
        http = config.get("http", {})
        return cls(
            cache_dir=config.get("caminhos", {}).get("cache", "cache"),
            base_url=http.get("base_url", API_URL),
            per_page=http.get("per_page", 100),
            max_tentativas=http.get("max_tentativas", 5),
            backoff_base_s=http.get("backoff_base_s", 1.0),
            timeout_s=http.get("timeout_s", 30.0),
            **kwargs,
        )

    # ------------------------------------------------------------------ API publica

    def get(self, caminho: str, params: dict | None = None, usar_cache: bool = True) -> Resposta:
        """GET de uma unica pagina. Erros 4xx viram ErroGitHub (404 etc. ficam no cache)."""
        url = montar_url(self.base_url, caminho, params)
        if usar_cache:
            em_cache = self.cache.ler(url)
            if em_cache is not None:
                return self._verificar(em_cache)
        resposta = self._requisitar(url)
        if usar_cache and (resposta.status < 400 or resposta.status in STATUS_CACHEAVEIS_DE_ERRO):
            self.cache.gravar(resposta)
        return self._verificar(resposta)

    def paginas(self, caminho: str, params: dict | None = None) -> Iterator[Resposta]:
        """Percorre todas as paginas seguindo o rel="next" do header Link."""
        params = {"per_page": self.per_page, **(params or {})}
        resposta = self.get(caminho, params)
        yield resposta
        while "next" in resposta.links:
            resposta = self.get(resposta.links["next"])
            yield resposta

    def get_todos(self, caminho: str, params: dict | None = None, chave: str | None = None) -> list:
        """Junta os itens de todas as paginas.

        `chave` e o campo da lista quando a resposta e um objeto, ex.: "items"
        (search), "workflows", "workflow_runs" ou "commits" (compare).
        """
        itens: list = []
        for resposta in self.paginas(caminho, params):
            itens.extend(resposta.dados[chave] if chave else resposta.dados)
        return itens

    def contar(self, caminho: str, params: dict | None = None) -> int:
        """Conta itens sem baixar a lista: per_page=1 e numero da pagina rel="last".

        Ex.: contar("/repos/o/r/contributors", {"anon": "true"}).
        """
        resposta = self.get(caminho, {**(params or {}), "per_page": 1})
        if "last" in resposta.links:
            return numero_da_pagina(resposta.links["last"]) or 0
        dados = resposta.dados
        return len(dados) if isinstance(dados, list) else int(bool(dados))

    def rate_limit(self) -> dict:
        """Situacao da cota (GET /rate_limit nao consome cota e nunca vai para o cache)."""
        return self._enviar(montar_url(self.base_url, "/rate_limit")).json()

    # ------------------------------------------------------------------ internos

    def _cabecalhos(self) -> dict[str, str]:
        cabecalhos = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if self.token:
            cabecalhos["Authorization"] = f"Bearer {self.token}"
        return cabecalhos

    def _enviar(self, url: str) -> requests.Response:
        self.chamadas_rede += 1
        return self.sessao.get(url, headers=self._cabecalhos(), timeout=self.timeout_s)

    def _requisitar(self, url: str) -> Resposta:
        """Faz a chamada repetindo em caso de rate limit (sem limite) e 5xx/rede (com limite)."""
        falhas = 0
        while True:
            try:
                r = self._enviar(url)
            except (requests.ConnectionError, requests.Timeout) as erro:
                falhas = self._esperar_backoff(falhas, url, str(erro))
                continue

            if self._e_rate_limit(r):
                self._esperar_rate_limit(r)
                continue
            if r.status_code >= 500:
                falhas = self._esperar_backoff(falhas, url, f"HTTP {r.status_code}")
                continue

            self._pausar_se_cota_acabou(r)
            try:
                dados = r.json() if r.content else None
            except ValueError:
                dados = {"message": r.text[:500]}
            return Resposta(r.status_code, url, dados, parse_link(r.headers.get("Link")))

    def _esperar_backoff(self, falhas: int, url: str, motivo: str) -> int:
        falhas += 1
        if falhas >= self.max_tentativas:
            raise ErroGitHub(0, url, f"{motivo} apos {falhas} tentativas")
        espera = self.backoff_base_s * 2 ** (falhas - 1)
        log.warning("%s em %s; tentativa %d/%d em %.0f s", motivo, url, falhas, self.max_tentativas, espera)
        self.dormir(espera)
        return falhas

    @staticmethod
    def _e_rate_limit(r: requests.Response) -> bool:
        """403/429 por cota primaria (Remaining=0) ou secundaria (Retry-After/mensagem)."""
        if r.status_code not in (403, 429):
            return False
        if r.headers.get("X-RateLimit-Remaining") == "0" or "Retry-After" in r.headers:
            return True
        return r.status_code == 429 or "rate limit" in r.text.lower()

    def _esperar_rate_limit(self, r: requests.Response) -> None:
        if "Retry-After" in r.headers:
            espera = float(r.headers["Retry-After"])
        elif "X-RateLimit-Reset" in r.headers:
            espera = float(r.headers["X-RateLimit-Reset"]) - self.agora()
        else:
            espera = self._espera_pela_rate_limit_api(r.url)
        espera = max(espera, 0) + 1  # 1 s de folga para o relogio do servidor
        log.warning("Rate limit atingido; aguardando %.0f s", espera)
        self.dormir(espera)

    def _espera_pela_rate_limit_api(self, url: str) -> float:
        """Sem headers de cota: pergunta ao /rate_limit quando o recurso certo renova."""
        try:
            recursos = self.rate_limit().get("resources", {})
        except (requests.RequestException, ValueError):
            return 60.0
        recurso = "search" if "/search/" in url else "core"
        reset = recursos.get(recurso, {}).get("reset")
        return float(reset) - self.agora() if reset else 60.0

    def _pausar_se_cota_acabou(self, r: requests.Response) -> None:
        """Se esta resposta consumiu a ultima chamada da cota, espera o reset antes da proxima."""
        if r.headers.get("X-RateLimit-Remaining") == "0" and "X-RateLimit-Reset" in r.headers:
            espera = max(float(r.headers["X-RateLimit-Reset"]) - self.agora(), 0) + 1
            log.warning("Cota esgotada; aguardando %.0f s ate o reset", espera)
            self.dormir(espera)

    @staticmethod
    def _verificar(resposta: Resposta) -> Resposta:
        if resposta.status >= 400:
            mensagem = resposta.dados.get("message", "") if isinstance(resposta.dados, dict) else ""
            raise ErroGitHub(resposta.status, resposta.url, mensagem)
        return resposta
