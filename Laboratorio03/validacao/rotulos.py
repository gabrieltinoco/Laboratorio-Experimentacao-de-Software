"""Formato das planilhas de rotulos, compartilhado pelo sorteio, concordancia e consenso."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ABA_REPOSITORIOS = "repositorios"
ABA_RELEASES = "releases"

# dimensao -> (aba, coluna, valores permitidos)
DIMENSOES = {
    "tipo_projeto": (ABA_REPOSITORIOS, "tipo_projeto",
                     ("biblioteca/framework", "aplicação/serviço", "ferramenta CLI", "outro")),
    "entregas_reais": (ABA_REPOSITORIOS, "entregas_reais", ("sim", "não", "incerto")),
    "corretiva": (ABA_RELEASES, "corretiva", ("sim", "não")),
}

CHAVES = {ABA_REPOSITORIOS: ["repositorio"], ABA_RELEASES: ["repositorio", "tag_name"]}


def caminho_rotulos(pasta: str | Path, avaliador: str) -> Path:
    return Path(pasta) / f"rotulos_{avaliador}.xlsx"


def normalizar(valor) -> str | None:
    """Rotulo sem espacos extras; celulas vazias viram None."""
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None
    texto = str(valor).strip()
    return texto or None


def ler_rotulos(caminho: str | Path) -> dict[str, pd.DataFrame]:
    """Abas de repositorios e releases, com os rotulos normalizados."""
    abas = pd.read_excel(caminho, sheet_name=[ABA_REPOSITORIOS, ABA_RELEASES], dtype=str)
    for aba, coluna, _ in DIMENSOES.values():
        abas[aba][coluna] = abas[aba][coluna].map(normalizar)
    return abas


def problemas_de_preenchimento(abas: dict[str, pd.DataFrame]) -> list[str]:
    """Celulas vazias ou com valor fora da lista permitida."""
    problemas = []
    for aba, coluna, permitidos in DIMENSOES.values():
        tabela = abas[aba]
        for _, linha in tabela.iterrows():
            valor = linha[coluna]
            if valor not in permitidos:
                item = " ".join(str(linha[c]) for c in CHAVES[aba])
                problemas.append(f"{aba}/{coluna}: {item} = {valor!r}")
    return problemas
