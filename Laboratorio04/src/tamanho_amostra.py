"""Discussao do tamanho da amostra (extra da entrega final).

Pergunta: com o efeito observado nos dados reais, qual o poder de cada teste
com o n coletado (30 por grupo) e quantas observacoes seriam precisas para
80% de poder?

Uso: python -m src.tamanho_amostra   # seed 42; grava results/tamanho_amostra.csv
"""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pandas as pd

from src.experimentos import ALPHA, N_REP, TESTES, _salvar, rodar_grade
from src.parametros import ajustar_por_grupo, carregar_prs, parametros_simulacao
from src.simulacao import gerar_dados

RAIZ = Path(__file__).resolve().parent.parent
ARQ_TAMANHO = RAIZ / "results" / "tamanho_amostra.csv"

NS = [30, 50, 100, 200, 400, 800, 1200, 1600]
PODER_ALVO = 0.80


def efeito_observado(df: pd.DataFrame | None = None) -> float:
    """Reducao relativa da mediana ajustada (e^mu) do grupo com bot."""
    ajuste = ajustar_por_grupo(carregar_prs() if df is None else df)
    return float(1 - ajuste.loc["com_bot", "mediana"] / ajuste.loc["sem_bot", "mediana"])


def poder_por_n(rng, efeito, ns=NS, n_rep=N_REP, alpha=ALPHA, params=None) -> pd.DataFrame:
    """Poder de cada teste para um efeito fixo, variando n por grupo."""
    params = params or parametros_simulacao()
    partes = [
        rodar_grade(
            {"base": gerar_dados}, TESTES, [efeito], n, rng,
            n_rep=n_rep, alpha=alpha, pergunta="tamanho_amostra", params=params,
        )
        for n in ns
    ]
    return pd.concat(partes, ignore_index=True)


def n_para_poder(df: pd.DataFrame, teste: str, alvo: float = PODER_ALVO) -> float | None:
    """n por grupo em que o poder cruza o alvo (interpolacao linear); None se nao cruza."""
    curva = df[df["teste"] == teste].sort_values("n_por_grupo")
    n = curva["n_por_grupo"].to_numpy(dtype=float)
    poder = curva["taxa_rejeicao"].to_numpy(dtype=float)
    acima = np.nonzero(poder >= alvo)[0]
    if acima.size == 0:
        return None
    i = acima[0]
    if i == 0:
        return float(n[0])
    return float(np.interp(alvo, [poder[i - 1], poder[i]], [n[i - 1], n[i]]))


def grafico_tamanho_amostra(df: pd.DataFrame, alvo: float = PODER_ALVO):
    """Poder x n por grupo, uma linha por teste (cores padrao), com IC 95%."""
    import plotly.graph_objects as go

    from src.estilo import CORES_TESTE, NOMES_TESTE, aplicar_layout

    fig = go.Figure()
    for teste in ("welch", "mann_whitney"):
        curva = df[df["teste"] == teste].sort_values("n_por_grupo")
        fig.add_trace(
            go.Scatter(
                x=curva["n_por_grupo"],
                y=curva["taxa_rejeicao"],
                mode="lines+markers",
                name=NOMES_TESTE[teste],
                line=dict(color=CORES_TESTE[teste], width=2),
                error_y=dict(
                    type="data",
                    symmetric=False,
                    array=curva["ic95_sup"] - curva["taxa_rejeicao"],
                    arrayminus=curva["taxa_rejeicao"] - curva["ic95_inf"],
                    thickness=1,
                ),
                hovertemplate="n = %{x}<br>poder = %{y:.3f}<extra>%{fullData.name}</extra>",
            )
        )
    fig.add_hline(
        y=alvo, line_dash="dash", line_color="#8a8f96",
        annotation_text=f"{alvo:.0%} de poder", annotation_position="bottom right",
    )
    ns = sorted(df["n_por_grupo"].unique())
    fig.update_xaxes(
        title_text="Observações por grupo (n, escala log)", type="log",
        tickmode="array", tickvals=ns, ticktext=[f"{n:,}".replace(",", ".") for n in ns],
    )
    fig.update_yaxes(title_text="Poder (proporção de rejeições)", range=[0, 1], tickformat=".0%")
    return aplicar_layout(fig, title="Poder com o efeito observado nos dados reais")


def main() -> None:
    rng = np.random.default_rng(42)
    inicio = time.perf_counter()
    efeito = efeito_observado()
    df = poder_por_n(rng, round(efeito, 3))
    _salvar(df, ARQ_TAMANHO)
    print(f"Efeito observado nos dados reais: {efeito:.3f}")
    print(df.pivot_table(index="n_por_grupo", columns="teste", values="taxa_rejeicao").round(4))
    for teste in TESTES:
        n80 = n_para_poder(df, teste)
        texto = f"{n80:.0f}" if n80 else f"> {NS[-1]}"
        print(f"n por grupo para 80% de poder ({teste}): {texto}")
    print(f"Gravado {ARQ_TAMANHO.relative_to(RAIZ)} ({time.perf_counter() - inicio:.1f} s)")


if __name__ == "__main__":
    main()
