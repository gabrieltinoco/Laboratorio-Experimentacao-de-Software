"""Testes da selecao, dos metadados e do funil com um cliente falso (sem rede)."""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest
import yaml

from pipeline import selecao
from pipeline.funil import Funil
from pipeline.http_client import ErroGitHub, Resposta
from pipeline.metadados import coletar_metadados, contar_contribuidores, idade_em_anos
from pipeline.selecao import (
    ETAPA_ACTIONS,
    ETAPA_METADADOS,
    buscar_candidatos,
    buscar_faixa,
    consulta_da_faixa,
    ordem_de_avaliacao,
    selecionar,
)


def repo(nome, estrelas=1500, linguagem="Python", criado_em="2020-09-30T12:00:00Z"):
    return {"full_name": nome, "html_url": f"https://github.com/{nome}", "stargazers_count": estrelas,
            "language": linguagem, "default_branch": "main", "created_at": criado_em}


class ClienteFalso:
    """Responde a busca por consulta e aos endpoints por repositorio.

    `busca`: {consulta: (total_count, [paginas de itens])}
    `workflows` / `contribuidores`: {nome: int ou ErroGitHub}
    """

    def __init__(self, busca=None, workflows=None, contribuidores=None):
        self.busca = busca or {}
        self.workflows = workflows or {}
        self.contribuidores = contribuidores or {}
        self.chamadas: list[str] = []

    def paginas(self, caminho, params=None):
        total, paginas = self.busca[params["q"]]
        for itens in paginas:
            self.chamadas.append(f"search {params['q']}")
            yield Resposta(200, caminho, {"total_count": total, "items": itens})

    def get(self, caminho, params=None):
        self.chamadas.append(caminho)
        nome = caminho.removeprefix("/repos/").removesuffix("/actions/workflows")
        valor = self.workflows[nome]
        if isinstance(valor, Exception):
            raise valor
        return Resposta(200, caminho, {"total_count": valor, "workflows": []})

    def contar(self, caminho, params=None):
        self.chamadas.append(caminho)
        valor = self.contribuidores.get(caminho.removeprefix("/repos/").removesuffix("/contributors"), 1)
        if isinstance(valor, Exception):
            raise valor
        return valor


def config(faixas=((1000, 1999), (2000, None)), maximo=10):
    return {"janela": {"inicio": "2025-10-01", "fim": "2026-09-30"},
            "selecao": {"faixas_estrelas": [list(f) for f in faixas], "max_repositorios": maximo, "semente": 42}}


Q1 = consulta_da_faixa(1000, 1999, "2025-10-01")
Q2 = consulta_da_faixa(2000, None, "2025-10-01")


# ---------------------------------------------------------------- busca


def test_consulta_da_faixa():
    assert Q1 == "stars:1000..1999 pushed:>=2025-10-01 archived:false"
    assert Q2 == "stars:>=2000 pushed:>=2025-10-01 archived:false"


def test_buscar_faixa_para_no_teto_de_1000():
    paginas = [[repo(f"o/r{p}-{i}") for i in range(100)] for p in range(12)]
    cliente = ClienteFalso(busca={Q1: (5000, paginas)})
    itens, total = buscar_faixa(cliente, Q1)
    assert len(itens) == 1000 and total == 5000
    assert len(cliente.chamadas) == 10


def test_buscar_candidatos_sem_duplicatas():
    cliente = ClienteFalso(busca={
        Q1: (2, [[repo("o/a"), repo("o/b")]]),
        Q2: (2, [[repo("o/b", estrelas=2001), repo("o/c", estrelas=3000)]]),
    })
    candidatos, encontrados = buscar_candidatos(cliente, config()["selecao"]["faixas_estrelas"], "2025-10-01")
    assert [c["full_name"] for c in candidatos] == ["o/a", "o/b", "o/c"]
    assert encontrados == 4


def test_ordem_de_avaliacao_e_reproduzivel_e_independe_da_ordem_da_busca():
    candidatos = [repo(f"o/r{i}") for i in range(30)]
    a = ordem_de_avaliacao(candidatos, 42)
    b = ordem_de_avaliacao(list(reversed(candidatos)), 42)
    assert [c["full_name"] for c in a] == [c["full_name"] for c in b]
    assert [c["full_name"] for c in a] != sorted(c["full_name"] for c in candidatos)
    assert a != ordem_de_avaliacao(candidatos, 7)


# ---------------------------------------------------------------- metadados


def test_idade_em_anos_relativa_ao_fim_da_janela():
    assert idade_em_anos("2020-09-30T12:00:00Z", date(2026, 9, 30)) == 6.0
    assert idade_em_anos("2026-09-30T00:00:00Z", date(2026, 9, 30)) == 0.0


def test_coletar_metadados():
    cliente = ClienteFalso(contribuidores={"o/a": 187})
    meta = coletar_metadados(cliente, repo("o/a", linguagem=None), date(2026, 9, 30))
    assert meta == {"repositorio": "o/a", "url": "https://github.com/o/a", "estrelas": 1500, "linguagem": "",
                    "default_branch": "main", "criado_em": "2020-09-30T12:00:00Z", "idade_anos": 6.0,
                    "contribuidores": 187}
    assert cliente.chamadas == ["/repos/o/a/contributors"]


def test_contribuidores_none_quando_github_recusa_listar():
    cliente = ClienteFalso(contribuidores={"o/a": ErroGitHub(403, "u", "list is too large")})
    assert contar_contribuidores(cliente, "o/a") is None


def test_contribuidores_propaga_outros_erros():
    cliente = ClienteFalso(contribuidores={"o/a": ErroGitHub(404, "u")})
    with pytest.raises(ErroGitHub):
        contar_contribuidores(cliente, "o/a")


# ---------------------------------------------------------------- selecao + funil


def cenario(maximo=10):
    cliente = ClienteFalso(
        busca={Q1: (3, [[repo("o/ok1"), repo("o/sem-actions"), repo("o/removido")]]),
               Q2: (2, [[repo("o/ok2", estrelas=5000), repo("o/sumiu", estrelas=2500)]])},
        workflows={"o/ok1": 3, "o/sem-actions": 0, "o/removido": ErroGitHub(404, "u"), "o/ok2": 1, "o/sumiu": 2},
        contribuidores={"o/sumiu": ErroGitHub(451, "u")},
    )
    return cliente, config(maximo=maximo)


def test_selecionar_aplica_etapas_e_registra_motivos():
    cliente, cfg = cenario()
    amostra, funil = selecionar(cliente, cfg)

    assert sorted(amostra["repositorio"]) == ["o/ok1", "o/ok2"]
    assert set(amostra.columns) >= {"estrelas", "linguagem", "default_branch", "idade_anos", "contribuidores",
                                    "workflows"}
    motivos = {d["repositorio"]: (d["etapa"], d["motivo"]) for d in funil.descartes}
    assert motivos == {
        "o/sem-actions": (ETAPA_ACTIONS, "sem workflows"),
        "o/removido": (ETAPA_ACTIONS, "erro ao listar workflows (HTTP 404)"),
        "o/sumiu": (ETAPA_METADADOS, "erro ao coletar metadados (HTTP 451)"),
    }


def test_sem_actions_nao_gasta_outras_chamadas():
    cliente, cfg = cenario()
    selecionar(cliente, cfg)
    assert "/repos/o/sem-actions/contributors" not in cliente.chamadas


def test_para_ao_atingir_max_repositorios():
    cliente, cfg = cenario(maximo=1)
    amostra, funil = selecionar(cliente, cfg)
    assert len(amostra) == 1
    tabela = funil.tabela().set_index("etapa")
    assert tabela.loc["candidatos avaliados", "repositorios"] == funil.avaliados < 5
    assert tabela.iloc[-1]["repositorios"] == 1


def test_criterios_extras_entram_no_funil():
    cliente, cfg = cenario()

    def poucas_releases(_, meta):
        return "menos de 5 releases na janela" if meta["repositorio"] == "o/ok2" else None

    amostra, funil = selecionar(cliente, cfg, criterios=[("criterio minimo", poucas_releases)])
    assert list(amostra["repositorio"]) == ["o/ok1"]
    tabela = funil.tabela().set_index("etapa")
    assert tabela.loc["criterio minimo", "motivos"] == "menos de 5 releases na janela (1)"
    assert tabela.loc["criterio minimo", "repositorios"] == 1


def test_falha_de_rede_interrompe_em_vez_de_descartar():
    cliente, cfg = cenario()
    cliente.workflows["o/ok1"] = ErroGitHub(0, "u", "HTTP 502 apos 5 tentativas")
    with pytest.raises(ErroGitHub):
        selecionar(cliente, cfg)


def test_falha_de_rede_nos_metadados_tambem_interrompe():
    cliente, cfg = cenario()
    cliente.contribuidores["o/ok1"] = ErroGitHub(0, "u")
    with pytest.raises(ErroGitHub):
        selecionar(cliente, cfg)


def test_tabela_do_funil():
    cliente, cfg = cenario()
    _, funil = selecionar(cliente, cfg)
    tabela = funil.tabela()
    assert list(tabela["etapa"]) == ["encontrados na busca", "candidatos coletados", "candidatos avaliados",
                                     ETAPA_ACTIONS, ETAPA_METADADOS]
    assert list(tabela["repositorios"]) == [5, 5, 5, 3, 2]
    assert list(tabela["descartados"]) == [0, 0, 0, 2, 1]
    acoes = tabela.set_index("etapa").loc[ETAPA_ACTIONS, "motivos"]
    assert "sem workflows (1)" in acoes and "HTTP 404" in acoes


def test_funil_rejeita_etapa_desconhecida():
    with pytest.raises(ValueError):
        Funil(etapas=[ETAPA_ACTIONS]).descartar("o/a", "outra", "x")


def test_funil_salva_csvs(tmp_path):
    cliente, cfg = cenario()
    _, funil = selecionar(cliente, cfg)
    funil.salvar(tmp_path / "dados")
    assert len(pd.read_csv(tmp_path / "dados" / "funil.csv")) == 5
    assert len(pd.read_csv(tmp_path / "dados" / "descartes.csv")) == 3


def test_main_grava_metadados_e_funil(tmp_path, monkeypatch):
    cliente, cfg = cenario()
    cfg["caminhos"] = {"dados": str(tmp_path / "dados"), "cache": str(tmp_path / "cache")}
    arquivo = tmp_path / "config.yaml"
    arquivo.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    monkeypatch.setattr(selecao.GitHubClient, "from_config", classmethod(lambda cls, c: cliente))

    selecao.main(["--config", str(arquivo)])

    assert len(pd.read_csv(tmp_path / "dados" / "metadados.csv")) == 2
    assert (tmp_path / "dados" / "funil.csv").exists()
