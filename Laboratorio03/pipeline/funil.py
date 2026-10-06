"""Funil de selecao: quantos repositorios restam em cada etapa e por que os demais sairam."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd


@dataclass
class Funil:
    etapas: list[str]
    encontrados_na_busca: int = 0
    candidatos: int = 0
    descartes: list[dict] = field(default_factory=list)
    aprovados: list[str] = field(default_factory=list)

    def descartar(self, repositorio: str, etapa: str, motivo: str) -> None:
        if etapa not in self.etapas:
            raise ValueError(f"Etapa desconhecida: {etapa}")
        self.descartes.append({"repositorio": repositorio, "etapa": etapa, "motivo": motivo})

    def aprovar(self, repositorio: str) -> None:
        self.aprovados.append(repositorio)

    @property
    def avaliados(self) -> int:
        return len(self.aprovados) + len(self.descartes)

    def tabela(self) -> pd.DataFrame:
        linhas = [
            {"etapa": "encontrados na busca", "repositorios": self.encontrados_na_busca,
             "descartados": 0, "motivos": ""},
            {"etapa": "candidatos coletados", "repositorios": self.candidatos,
             "descartados": self.encontrados_na_busca - self.candidatos,
             "motivos": "teto de 1.000 resultados por consulta da busca"},
            {"etapa": "candidatos avaliados", "repositorios": self.avaliados,
             "descartados": self.candidatos - self.avaliados,
             "motivos": "nao avaliados: amostra atingiu o tamanho maximo"},
        ]
        restantes = self.avaliados
        for etapa in self.etapas:
            motivos = Counter(d["motivo"] for d in self.descartes if d["etapa"] == etapa)
            descartados = sum(motivos.values())
            restantes -= descartados
            linhas.append({
                "etapa": etapa,
                "repositorios": restantes,
                "descartados": descartados,
                "motivos": "; ".join(f"{m} ({n})" for m, n in motivos.most_common()),
            })
        return pd.DataFrame(linhas)

    def salvar(self, pasta: str | Path) -> None:
        pasta = Path(pasta)
        pasta.mkdir(parents=True, exist_ok=True)
        self.tabela().to_csv(pasta / "funil.csv", index=False)
        pd.DataFrame(self.descartes, columns=["repositorio", "etapa", "motivo"]).to_csv(
            pasta / "descartes.csv", index=False)
