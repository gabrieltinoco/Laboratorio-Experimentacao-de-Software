"""Avalia e registra a heurística corretiva frente ao consenso humano.

Uso: python -m validacao.avaliar_heuristica --config config.yaml --versao v1
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
import yaml

from metricas.corretiva import HEURISTICAS, VERSAO_ATUAL


def ler_jsonl(caminho: Path) -> list[dict]:
    with caminho.open(encoding="utf-8") as arquivo:
        return [json.loads(linha) for linha in arquivo if linha.strip()]


def _predicoes(
    releases: list[dict], comparacoes: list[dict], versao: str = VERSAO_ATUAL
) -> dict[tuple[str, str], bool]:
    heuristica = HEURISTICAS[versao]
    por_repositorio: dict[str, list[dict]] = {}
    for release in releases:
        if not release.get("draft") and not release.get("prerelease") and release.get("published_at"):
            por_repositorio.setdefault(release["repositorio"], []).append(release)

    mensagens = {
        (comparacao["repositorio"], comparacao["tag_release"]): [
            commit.get("message") for commit in comparacao.get("commits", [])
        ]
        for comparacao in comparacoes
        if comparacao.get("tag_release")
    }
    predicoes = {}
    for repositorio, releases_repo in por_repositorio.items():
        ordenadas = sorted(
            releases_repo,
            key=lambda release: (release["published_at"], str(release.get("tag_name", ""))),
        )
        anterior = None
        for release in ordenadas:
            tag = release.get("tag_name")
            if tag:
                predicoes[(repositorio, tag)] = heuristica(
                    anterior,
                    tag,
                    mensagens.get((repositorio, tag), []),
                    release.get("body"),
                )
            anterior = tag
    return predicoes


def avaliar(
    consenso: pd.DataFrame,
    releases: list[dict],
    comparacoes: list[dict],
    versao: str = VERSAO_ATUAL,
) -> dict[str, float | int]:
    """Calcula precisão, recall e F1 usando apenas os rótulos de consenso."""
    colunas = {"repositorio", "tag_name", "corretiva"}
    if not colunas.issubset(consenso.columns):
        raise ValueError(f"O consenso deve conter as colunas: {', '.join(sorted(colunas))}.")
    if consenso.duplicated(["repositorio", "tag_name"]).any():
        raise ValueError("O consenso contém chaves duplicadas de repositório e tag.")
    rotulos = consenso["corretiva"].astype(str).str.strip()
    if not rotulos.isin({"sim", "não"}).all():
        raise ValueError("O consenso contém rótulos corretivos diferentes de 'sim' ou 'não'.")
    if consenso.empty:
        raise ValueError("O consenso não contém releases rotuladas.")

    if versao not in HEURISTICAS:
        raise ValueError(f"Versão desconhecida: {versao!r}; disponíveis: {', '.join(HEURISTICAS)}.")
    predicoes = _predicoes(releases, comparacoes, versao)
    chaves = list(zip(consenso["repositorio"].astype(str), consenso["tag_name"].astype(str)))
    sem_predicao = [chave for chave in chaves if chave not in predicoes]
    if sem_predicao:
        raise ValueError(f"Sem releases coletadas para {len(sem_predicao)} rótulo(s) do consenso.")

    reais = rotulos.eq("sim").tolist()
    previstas = [predicoes[chave] for chave in chaves]
    verdadeiros_positivos = sum(real and previsto for real, previsto in zip(reais, previstas))
    falsos_positivos = sum(not real and previsto for real, previsto in zip(reais, previstas))
    falsos_negativos = sum(real and not previsto for real, previsto in zip(reais, previstas))
    precisao = (
        verdadeiros_positivos / (verdadeiros_positivos + falsos_positivos)
        if verdadeiros_positivos + falsos_positivos
        else 0.0
    )
    recall = (
        verdadeiros_positivos / (verdadeiros_positivos + falsos_negativos)
        if verdadeiros_positivos + falsos_negativos
        else 0.0
    )
    f1 = 2 * precisao * recall / (precisao + recall) if precisao + recall else 0.0
    return {
        "n": len(consenso),
        "verdadeiros_positivos": verdadeiros_positivos,
        "falsos_positivos": falsos_positivos,
        "falsos_negativos": falsos_negativos,
        "precisao": precisao,
        "recall": recall,
        "f1": f1,
    }


def particionar(consenso: pd.DataFrame, semente: int) -> dict[str, pd.DataFrame]:
    """Metade dos repositórios para desenhar heurísticas, a outra para testá-las."""
    repositorios = pd.Series(sorted(consenso["repositorio"].unique()))
    desenvolvimento = set(repositorios.sample(n=len(repositorios) // 2, random_state=semente))
    na_metade = consenso["repositorio"].isin(desenvolvimento)
    return {"desenvolvimento": consenso[na_metade], "teste": consenso[~na_metade]}


def registrar(caminho: str | Path, versao: str, resultado: dict) -> None:
    """Acrescenta a avaliação sem sobrescrever uma versão já registrada."""
    caminho = Path(caminho)
    if not versao.strip():
        raise ValueError("A versão da heurística não pode ser vazia.")
    historico = pd.read_csv(caminho) if caminho.exists() else pd.DataFrame()
    if not historico.empty and historico["versao"].eq(versao).any():
        raise ValueError(f"A versão {versao!r} já foi registrada em {caminho}.")
    linha = pd.DataFrame([{"versao": versao, **resultado}])
    pd.concat([historico, linha], ignore_index=True).to_csv(caminho, index=False)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Avalia a heurística frente ao consenso.")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--versao", default=VERSAO_ATUAL, choices=sorted(HEURISTICAS))
    parser.add_argument(
        "--particao",
        choices=["desenvolvimento", "teste"],
        help="avalia só uma metade dos repositórios da amostra-ouro (registrada como versao@particao)",
    )
    args = parser.parse_args(argv)
    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    dados = Path(config["caminhos"]["dados"])
    pasta_validacao = Path(config["validacao"]["pasta"])
    consenso = pd.read_csv(pasta_validacao / "consenso_releases.csv", dtype=str)
    rotulo = args.versao
    if args.particao:
        consenso = particionar(consenso, config["validacao"]["semente"])[args.particao]
        rotulo = f"{args.versao}@{args.particao}"
    resultado = avaliar(
        consenso,
        ler_jsonl(dados / "releases.jsonl"),
        ler_jsonl(dados / "commits_entre_releases.jsonl"),
        args.versao,
    )
    destino = pasta_validacao / "avaliacao_heuristica.csv"
    registrar(destino, rotulo, resultado)
    print(
        f"{rotulo}: P={resultado['precisao']:.3f}, "
        f"R={resultado['recall']:.3f}, F1={resultado['f1']:.3f} "
        f"(n={resultado['n']}); histórico: {destino}"
    )


if __name__ == "__main__":
    main()
