"""RQ 06 (subgrupos) e RQ 07 (sensibilidade das categorias DORA).

Uso: python -m analise.rq06_rq07 [--dados dados/repositorios.csv]
"""

from __future__ import annotations

from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kruskal
from sklearn.metrics import cohen_kappa_score
from statsmodels.stats.multitest import multipletests

from analise.comum import (
    argumentos,
    classificar,
    ler_dataset,
    salvar_tabela,
)
from metricas.classificacao import CATEGORIAS as CATEGORIAS_DORA

METRICAS = {
    "deploy_freq_semana": "frequencia",
    "lead_time_release_dias": "lead_time_release",
    "lead_time_commit_dias": "lead_time_commit",
    "cfr_ci": "cfr_ci",
    "cfr_releases": "cfr_releases",
    "recuperacao_horas": "recuperacao",
}
FATORES = ("linguagem", "quartil_estrelas", "quartil_idade")
ROTULOS_ROMANO = (
    (0.147, "desprezível"),
    (0.33, "pequeno"),
    (0.474, "médio"),
)
COMBINACOES = {
    "C1": ("deploy_freq_semana", "lead_time_release_dias", "cfr_ci"),
    "C2": (
        "deploy_freq_com_prereleases_semana",
        "lead_time_commit_dias",
        "cfr_releases",
    ),
    "C3": ("deploy_freq_tags_semana", "lead_time_commit_dias", "cfr_ci"),
}
CATEGORIAS_ANALISADAS = (
    "categoria_frequencia",
    "categoria_lead_time",
    "categoria_cfr",
    "categoria_recuperacao",
    "categoria_geral",
)


def _quartis(serie: pd.Series) -> pd.Series:
    resultado = pd.Series(pd.NA, index=serie.index, dtype="string")
    validos = serie.notna()
    if validos.any():
        resultado.loc[validos] = pd.qcut(
            serie.loc[validos].rank(method="first"),
            q=4,
            labels=["Q1", "Q2", "Q3", "Q4"],
        ).astype("string")
    return resultado


def preparar_fatores(
    df: pd.DataFrame, tipo_projeto: pd.Series | None = None
) -> pd.DataFrame:
    """Cria fatores observáveis e inclui rótulos de projeto consensuais se fornecidos."""
    preparado = df.copy()
    preparado["linguagem"] = preparado["linguagem"].fillna("Não informada")
    preparado["quartil_estrelas"] = _quartis(preparado["estrelas"])
    preparado["quartil_idade"] = _quartis(preparado["idade_anos"])
    if tipo_projeto is not None:
        preparado["tipo_projeto"] = tipo_projeto.reindex(preparado.index)
    return preparado


def interpretar_cliff(delta: float) -> str:
    magnitude = abs(delta)
    for limite, interpretacao in ROTULOS_ROMANO:
        if magnitude < limite:
            return interpretacao
    return "grande"


def _grupos(serie: pd.Series, valores: pd.Series) -> dict[str, np.ndarray]:
    pares = pd.DataFrame({"grupo": serie, "valor": valores}).dropna()
    return {
        str(grupo): parte["valor"].to_numpy(dtype=float)
        for grupo, parte in pares.groupby("grupo", observed=True)
        if len(parte) >= 2
    }


def delta_cliff(primeiro: pd.Series | np.ndarray, segundo: pd.Series | np.ndarray) -> float:
    """Cliff's delta: P(primeiro > segundo) - P(primeiro < segundo)."""
    a = np.asarray(primeiro, dtype=float)
    b = np.asarray(segundo, dtype=float)
    comparacoes = a[:, None] - b[None, :]
    return float((np.count_nonzero(comparacoes > 0) - np.count_nonzero(comparacoes < 0))
                 / comparacoes.size)


def analisar_rq06(
    df: pd.DataFrame, tipo_projeto: pd.Series | None = None
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Kruskal-Wallis por fator/métrica, Holm global e efeitos Cliff pareados."""
    preparado = preparar_fatores(df, tipo_projeto)
    fatores = FATORES + (("tipo_projeto",) if tipo_projeto is not None else ())
    testes: list[dict] = []
    efeitos: list[dict] = []
    for fator in fatores:
        for coluna, metrica in METRICAS.items():
            grupos = _grupos(preparado[fator], preparado[coluna])
            n = sum(map(len, grupos.values()))
            base = {
                "fator": fator,
                "metrica": metrica,
                "n": n,
                "grupos": len(grupos),
                "contagens_grupo": "; ".join(
                    f"{nome}={len(valores)}" for nome, valores in grupos.items()
                ),
            }
            if len(grupos) < 2:
                testes.append({
                    **base, "h": None, "p_valor": None, "epsilon_quadrado": None,
                    "p_holm": None, "significativo_holm": False,
                })
                continue
            h, p = kruskal(*grupos.values())
            testes.append({
                **base,
                "h": float(h),
                "p_valor": float(p),
                "epsilon_quadrado": float(h / (n - 1)) if n > 1 else None,
                "p_holm": None,
                "significativo_holm": False,
            })
            for (grupo_a, valores_a), (grupo_b, valores_b) in combinations(grupos.items(), 2):
                delta = delta_cliff(valores_a, valores_b)
                efeitos.append({
                    "fator": fator,
                    "metrica": metrica,
                    "grupo_a": grupo_a,
                    "grupo_b": grupo_b,
                    "n_a": len(valores_a),
                    "n_b": len(valores_b),
                    "cliffs_delta": delta,
                    "magnitude_romano": interpretar_cliff(delta),
                })

    tabela = pd.DataFrame(testes)
    validos = tabela["p_valor"].notna()
    if validos.any():
        rejeitar, ajustados, _, _ = multipletests(
            tabela.loc[validos, "p_valor"].to_numpy(), method="holm"
        )
        tabela.loc[validos, "p_holm"] = ajustados
        tabela.loc[validos, "significativo_holm"] = rejeitar
    return tabela, pd.DataFrame(efeitos)


def classificar_combinacoes(df: pd.DataFrame) -> pd.DataFrame:
    """Classifica cada repositório em C1 (referência), C2 e C3."""
    saidas = []
    for nome, (frequencia, lead_time, cfr) in COMBINACOES.items():
        classes = classificar(df, frequencia, lead_time, cfr)
        classes = classes.rename(
            columns={
                coluna: f"{nome}_{coluna}"
                for coluna in classes.columns
                if coluna.startswith("categoria_")
            }
        )
        saidas.append(classes)
    resultado = saidas[0]
    for tabela in saidas[1:]:
        resultado = resultado.merge(tabela, on="repositorio", validate="one_to_one")
    return resultado


def analisar_rq07(classificacoes: pd.DataFrame) -> pd.DataFrame:
    """Mudança de categoria e kappa ponderado por métrica e categoria geral."""
    linhas = []
    for (combinacao_a, combinacao_b) in combinations(COMBINACOES, 2):
        for categoria in CATEGORIAS_ANALISADAS:
            coluna_a = f"{combinacao_a}_categoria_{categoria.removeprefix('categoria_')}"
            coluna_b = f"{combinacao_b}_categoria_{categoria.removeprefix('categoria_')}"
            pares = classificacoes[[coluna_a, coluna_b]].dropna()
            if pares.empty:
                mudaram = 0
                percentual = None
                kappa = None
            else:
                mudaram = int((pares[coluna_a] != pares[coluna_b]).sum())
                percentual = 100 * mudaram / len(pares)
                kappa = cohen_kappa_score(
                    pares[coluna_a],
                    pares[coluna_b],
                    labels=list(CATEGORIAS_DORA),
                    weights="linear",
                )
            linhas.append({
                "combinacao_a": combinacao_a,
                "combinacao_b": combinacao_b,
                "categoria": categoria.removeprefix("categoria_"),
                "n_pareado": len(pares),
                "n_mudaram": mudaram,
                "pct_mudaram": percentual,
                "kappa_ponderado_linear": kappa,
            })
    return pd.DataFrame(linhas)


def _tipo_projeto_consensual(pasta_validacao: Path, repositorios: pd.Series) -> pd.Series | None:
    """Lê consenso final ou usa apenas rótulos idênticos entre avaliadores."""
    consenso = pasta_validacao / "consenso_repositorios.csv"
    if consenso.exists():
        rotulos = pd.read_csv(consenso, dtype=str).set_index("repositorio")["tipo_projeto"]
        return repositorios.map(rotulos)

    avaliadores = [
        pasta_validacao / "rotulos_avaliador_1.xlsx",
        pasta_validacao / "rotulos_avaliador_2.xlsx",
    ]
    if not all(caminho.exists() for caminho in avaliadores):
        return None
    pares = []
    for caminho in avaliadores:
        rotulos = pd.read_excel(caminho, sheet_name="repositorios", dtype=str)
        pares.append(rotulos[["repositorio", "tipo_projeto"]].rename(
            columns={"tipo_projeto": caminho.stem}
        ))
    comparacao = pares[0].merge(pares[1], on="repositorio", validate="one_to_one")
    iguais = comparacao[comparacao.iloc[:, 1] == comparacao.iloc[:, 2]].set_index("repositorio")
    unicos = iguais.iloc[:, 0]
    return repositorios.map(unicos)


def executar(df: pd.DataFrame, saidas: str | Path) -> None:
    pasta = Path(saidas)
    raiz = Path(__file__).resolve().parents[1]
    tipo_projeto = _tipo_projeto_consensual(
        raiz / "validacao", df["repositorio"]
    )
    testes, efeitos = analisar_rq06(df, tipo_projeto)
    classes = classificar_combinacoes(df)
    sensibilidade = analisar_rq07(classes)
    salvar_tabela(testes, "rq06_kruskal_holm", pasta)
    tabela_testes = testes.astype(object).copy()
    for coluna in ("p_valor", "p_holm"):
        tabela_testes[coluna] = tabela_testes[coluna].map(
            lambda valor: (
                ""
                if valor is None or pd.isna(valor)
                else "<0.001"
                if float(valor) < 0.001
                else f"{float(valor):.4f}"
            )
        )
    (pasta / "rq06_kruskal_holm.md").write_text(
        tabela_testes.to_markdown(index=False, floatfmt=".3f") + "\n",
        encoding="utf-8",
    )
    salvar_tabela(efeitos, "rq06_cliff_romano", pasta)
    salvar_tabela(classes, "rq07_classificacoes_c1_c2_c3", pasta)
    salvar_tabela(sensibilidade, "rq07_sensibilidade", pasta)


def main(argv: list[str] | None = None) -> None:
    args = argumentos("RQ 06 e RQ 07: subgrupos e sensibilidade.", argv)
    executar(ler_dataset(args.dados), args.saidas)


if __name__ == "__main__":
    main()
