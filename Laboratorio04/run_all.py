"""Executa o pipeline reproduzível do Lab04 a partir dos dados versionados."""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pandas as pd

from src.experimentos import (
    ARQ_RESULTADOS,
    ARQ_RESULTADOS_ALPHA001,
    resumo,
    rodar_todas,
)
from src.parametros import carregar_prs, parametros_simulacao

SEMENTE = 42


def _salvar_resultados(df: pd.DataFrame, caminho: Path) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    df.round(
        {"taxa_rejeicao": 4, "ic95_inf": 4, "ic95_sup": 4}
    ).to_csv(caminho, index=False)


def main() -> None:
    inicio = time.perf_counter()
    rng = np.random.default_rng(SEMENTE)

    dados_reais = carregar_prs()
    parametros = parametros_simulacao(dados_reais)
    print(
        "Parametros ajustados aos dados reais: "
        f"mediana = {parametros['mediana']:.2f} h, "
        f"sigma = {parametros['sigma']:.3f}"
    )

    resultados = rodar_todas(rng, params=parametros)
    _salvar_resultados(resultados, ARQ_RESULTADOS)
    print(f"\nResultados com alpha = 0,05: {ARQ_RESULTADOS.name}")
    print(resumo(resultados))

    resultados_alpha001 = rodar_todas(rng, params=parametros, alpha=0.01)
    _salvar_resultados(resultados_alpha001, ARQ_RESULTADOS_ALPHA001)
    print(f"\nResultados com alpha = 0,01: {ARQ_RESULTADOS_ALPHA001.name}")
    print(resumo(resultados_alpha001))
    print(f"\nPipeline concluido em {time.perf_counter() - inicio:.1f} s.")


if __name__ == "__main__":
    main()
