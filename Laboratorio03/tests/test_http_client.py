"""Testes do cliente HTTP com respostas simuladas: nenhum teste vai a rede."""

from __future__ import annotations

import json

import pytest
import requests

from pipeline.http_client import (
    ErroGitHub,
    GitHubClient,
    montar_url,
    numero_da_pagina,
    parse_link,
)

API = "https://api.github.com"


def resposta_falsa(status=200, corpo=None, headers=None, url=""):
    r = requests.Response()
    r.status_code = status
    r._content = b"" if corpo is None else json.dumps(corpo).encode()
    r.headers.update(headers or {})
    r.url = url
    return r


class SessaoFalsa:
    """Devolve as respostas na ordem; um Exception na fila e lancado no lugar."""

    def __init__(self, *respostas):
        self.fila = list(respostas)
        self.chamadas: list[tuple[str, dict]] = []

    def get(self, url, headers=None, timeout=None):
        self.chamadas.append((url, headers))
        item = self.fila.pop(0)
        if isinstance(item, Exception):
            raise item
        item.url = url
        return item


@pytest.fixture
def esperas():
    return []


@pytest.fixture
def cliente(tmp_path, esperas):
    def criar(*respostas, token="tok-secreto", agora=1_000.0):
        sessao = SessaoFalsa(*respostas)
        c = GitHubClient(token=token, cache_dir=tmp_path / "cache", sessao=sessao,
                         dormir=esperas.append, agora=lambda: agora)
        return c, sessao
    return criar


# ---------------------------------------------------------------- utilitarios


def test_parse_link_extrai_next_e_last():
    header = ('<https://api.github.com/x?page=2>; rel="next", '
              '<https://api.github.com/x?page=7>; rel="last"')
    links = parse_link(header)
    assert links["next"].endswith("page=2")
    assert numero_da_pagina(links["last"]) == 7
    assert parse_link(None) == {}


def test_montar_url_e_canonica_independente_da_ordem_dos_params():
    a = montar_url(API, "/repos/o/r/releases", {"per_page": 100, "page": 2})
    b = montar_url(API, "repos/o/r/releases?page=2", {"per_page": "100"})
    assert a == b == f"{API}/repos/o/r/releases?page=2&per_page=100"


def test_montar_url_ignora_params_none():
    assert montar_url(API, "/x", {"a": None}) == f"{API}/x"


# ---------------------------------------------------------------- autenticacao e cache


def test_envia_token_e_nao_grava_token_no_cache(cliente, tmp_path):
    c, sessao = cliente(resposta_falsa(200, {"ok": True}))
    assert c.get("/repos/o/r").dados == {"ok": True}
    assert sessao.chamadas[0][1]["Authorization"] == "Bearer tok-secreto"
    for arquivo in (tmp_path / "cache").rglob("*.json"):
        assert "tok-secreto" not in arquivo.read_text(encoding="utf-8")


def test_token_vem_do_ambiente(monkeypatch, tmp_path):
    monkeypatch.setenv("GITHUB_TOKEN", "do-ambiente")
    assert GitHubClient(cache_dir=tmp_path).token == "do-ambiente"


def test_sem_token_nao_envia_authorization(monkeypatch, cliente):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    c, sessao = cliente(resposta_falsa(200, []), token="")
    c.get("/x")
    assert "Authorization" not in sessao.chamadas[0][1]


def test_cache_organizado_por_repositorio(cliente, tmp_path):
    c, _ = cliente(resposta_falsa(200, []))
    c.get("/repos/dono/projeto/releases")
    assert list((tmp_path / "cache" / "repos" / "dono__projeto").glob("*.json"))


def test_retomada_nao_repete_chamadas_ja_feitas(cliente, tmp_path, esperas):
    c, sessao = cliente(resposta_falsa(200, {"n": 1}))
    c.get("/repos/o/r")
    # "Reinicia" a coleta: novo cliente, mesmo diretorio, sessao sem respostas.
    novo = GitHubClient(token="t", cache_dir=tmp_path / "cache", sessao=SessaoFalsa())
    resposta = novo.get("/repos/o/r")
    assert resposta.dados == {"n": 1} and resposta.do_cache
    assert novo.chamadas_rede == 0


def test_usar_cache_false_vai_a_rede(cliente):
    c, sessao = cliente(resposta_falsa(200, 1), resposta_falsa(200, 2))
    c.get("/x")
    assert c.get("/x", usar_cache=False).dados == 2
    assert len(sessao.chamadas) == 2


def test_cache_corrompido_e_refeito(cliente):
    c, sessao = cliente(resposta_falsa(200, {"v": 1}))
    arquivo = c.cache.caminho(montar_url(API, "/x"))
    arquivo.parent.mkdir(parents=True)
    arquivo.write_text("{meio json", encoding="utf-8")
    assert c.get("/x").dados == {"v": 1}
    assert len(sessao.chamadas) == 1


# ---------------------------------------------------------------- erros 4xx


def test_404_vira_erro_e_fica_no_cache(cliente):
    c, sessao = cliente(resposta_falsa(404, {"message": "Not Found"}))
    for _ in range(2):
        with pytest.raises(ErroGitHub) as erro:
            c.get("/repos/o/r/compare/v1...v2")
        assert erro.value.status == 404
    assert len(sessao.chamadas) == 1  # a segunda vez veio do cache


def test_403_sem_rate_limit_nao_e_repetido_nem_cacheado(cliente, esperas):
    c, sessao = cliente(resposta_falsa(403, {"message": "Forbidden"}, {"X-RateLimit-Remaining": "4000"}),
                        resposta_falsa(200, {}))
    with pytest.raises(ErroGitHub):
        c.get("/x")
    assert esperas == []
    c.get("/x")  # nao estava no cache: vai a rede
    assert len(sessao.chamadas) == 2


def test_corpo_nao_json_vira_mensagem(cliente):
    r = resposta_falsa(404)
    r._content = b"<html>nao encontrado</html>"
    c, _ = cliente(r)
    with pytest.raises(ErroGitHub, match="nao encontrado"):
        c.get("/x")


# ---------------------------------------------------------------- backoff


def test_backoff_exponencial_em_5xx(cliente, esperas):
    c, _ = cliente(resposta_falsa(502), resposta_falsa(503), resposta_falsa(500),
                   resposta_falsa(200, {"ok": 1}))
    assert c.get("/x").dados == {"ok": 1}
    assert esperas == [1, 2, 4]


def test_desiste_apos_max_tentativas(cliente, esperas):
    c, sessao = cliente(*[resposta_falsa(500) for _ in range(5)])
    with pytest.raises(ErroGitHub, match="5 tentativas"):
        c.get("/x")
    assert esperas == [1, 2, 4, 8]
    assert len(sessao.chamadas) == 5


def test_erro_de_rede_tambem_tem_backoff(cliente, esperas):
    c, _ = cliente(requests.ConnectionError("caiu"), requests.Timeout("lento"),
                   resposta_falsa(200, []))
    assert c.get("/x").dados == []
    assert esperas == [1, 2]


def test_5xx_nao_vai_para_o_cache(cliente):
    c, _ = cliente(*[resposta_falsa(500) for _ in range(5)])
    with pytest.raises(ErroGitHub):
        c.get("/x")
    assert not list(c.cache.raiz.rglob("*.json"))


# ---------------------------------------------------------------- rate limit


def test_espera_ate_o_reset_quando_cota_acaba(cliente, esperas):
    bloqueio = resposta_falsa(403, {"message": "API rate limit exceeded"},
                              {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1300"})
    c, _ = cliente(bloqueio, resposta_falsa(200, {"ok": 1}), agora=1_000.0)
    assert c.get("/x").dados == {"ok": 1}
    assert esperas == [301]  # 1300 - 1000 + 1 s de folga


def test_rate_limit_secundario_respeita_retry_after(cliente, esperas):
    c, _ = cliente(resposta_falsa(429, {}, {"Retry-After": "30"}), resposta_falsa(200, []))
    c.get("/x")
    assert esperas == [31]


def test_sem_headers_consulta_rate_limit(cliente, esperas):
    bloqueio = resposta_falsa(403, {"message": "You have exceeded a secondary rate limit"})
    situacao = resposta_falsa(200, {"resources": {"search": {"reset": 1_050}, "core": {"reset": 9_999}}})
    c, sessao = cliente(bloqueio, situacao, resposta_falsa(200, {"items": []}), agora=1_000.0)
    c.get("/search/repositories", {"q": "stars:>1000"})
    assert sessao.chamadas[1][0] == f"{API}/rate_limit"
    assert esperas == [51]  # usou o reset do recurso "search", nao do "core"


def test_rate_limit_api_fora_do_ar_espera_padrao(cliente, esperas):
    bloqueio = resposta_falsa(429, {})
    c, _ = cliente(bloqueio, requests.ConnectionError("x"), resposta_falsa(200, []))
    c.get("/x")
    assert esperas == [61]


def test_pausa_preventiva_quando_ultima_chamada_da_cota(cliente, esperas):
    ultima = resposta_falsa(200, {"ok": 1}, {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1100"})
    c, _ = cliente(ultima, agora=1_000.0)
    assert c.get("/x").dados == {"ok": 1}
    assert esperas == [101]


def test_reset_no_passado_nao_gera_espera_negativa(cliente, esperas):
    bloqueio = resposta_falsa(403, {}, {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "500"})
    c, _ = cliente(bloqueio, resposta_falsa(200, []), agora=1_000.0)
    c.get("/x")
    assert esperas == [1]


# ---------------------------------------------------------------- paginacao


def _link(pagina, ultima):
    partes = []
    if pagina < ultima:
        partes.append(f'<{API}/repos/o/r/releases?page={pagina + 1}&per_page=100>; rel="next"')
    partes.append(f'<{API}/repos/o/r/releases?page={ultima}&per_page=100>; rel="last"')
    return {"Link": ", ".join(partes)}


def test_get_todos_segue_link_next(cliente):
    c, sessao = cliente(resposta_falsa(200, [1, 2], _link(1, 3)),
                        resposta_falsa(200, [3, 4], _link(2, 3)),
                        resposta_falsa(200, [5], {}))
    assert c.get_todos("/repos/o/r/releases") == [1, 2, 3, 4, 5]
    assert "per_page=100" in sessao.chamadas[0][0]
    assert "page=2" in sessao.chamadas[1][0]


def test_get_todos_com_chave_de_objeto(cliente):
    c, _ = cliente(resposta_falsa(200, {"total_count": 3, "workflow_runs": [1, 2]}, _link(1, 2)),
                   resposta_falsa(200, {"total_count": 3, "workflow_runs": [3]}))
    assert c.get_todos("/repos/o/r/actions/runs", {"event": "push"}, chave="workflow_runs") == [1, 2, 3]


def test_paginacao_e_retomada_pagina_a_pagina(cliente, tmp_path):
    c, _ = cliente(resposta_falsa(200, [1], _link(1, 2)), resposta_falsa(200, [2]))
    c.get_todos("/repos/o/r/releases")
    novo = GitHubClient(token="t", cache_dir=tmp_path / "cache", sessao=SessaoFalsa())
    assert novo.get_todos("/repos/o/r/releases") == [1, 2]
    assert novo.chamadas_rede == 0


def test_contar_le_ultima_pagina(cliente):
    c, sessao = cliente(resposta_falsa(200, [{"login": "a"}], {
        "Link": f'<{API}/repos/o/r/contributors?anon=true&page=2&per_page=1>; rel="next", '
                f'<{API}/repos/o/r/contributors?anon=true&page=187&per_page=1>; rel="last"'}))
    assert c.contar("/repos/o/r/contributors", {"anon": "true"}) == 187
    assert "per_page=1" in sessao.chamadas[0][0]


def test_contar_sem_link_usa_tamanho_da_lista(cliente):
    c, _ = cliente(resposta_falsa(200, [{"login": "unico"}]))
    assert c.contar("/repos/o/r/contributors") == 1


def test_contar_repositorio_vazio(cliente):
    c, _ = cliente(resposta_falsa(204))
    assert c.contar("/repos/o/r/contributors") == 0


# ---------------------------------------------------------------- configuracao


def test_from_config(tmp_path):
    config = {"http": {"per_page": 50, "max_tentativas": 3, "backoff_base_s": 2},
              "caminhos": {"cache": str(tmp_path / "c")}}
    c = GitHubClient.from_config(config, token="t")
    assert (c.per_page, c.max_tentativas, c.backoff_base_s) == (50, 3, 2)
    assert c.cache.raiz == tmp_path / "c"
