"""Gráficos do Lab04, com cores e layout compartilhados."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from numpy.typing import ArrayLike
from plotly.subplots import make_subplots
from scipy import stats

from src.estilo import CORES_GRUPO, CORES_TESTE, NOMES_GRUPO, NOMES_TESTE, aplicar_layout
from src.testes import Resultado, teste_mann_whitney, teste_welch

GRUPOS = ("sem_bot", "com_bot")
COLUNAS_DADOS = {"grupo", "horas_ate_merge"}


def _validar_dados(df: pd.DataFrame, origem: str) -> None:
    faltantes = COLUNAS_DADOS.difference(df.columns)
    if faltantes:
        raise ValueError(f"{origem} não contém as colunas obrigatórias: {sorted(faltantes)}")

    grupos = set(df["grupo"].dropna().unique())
    if grupos != set(GRUPOS):
        raise ValueError(f"{origem} deve conter exatamente os grupos {GRUPOS}")

    valores = df["horas_ate_merge"].to_numpy(dtype=float)
    if not np.isfinite(valores).all() or np.any(valores <= 0):
        raise ValueError(f"{origem} deve conter tempos de merge positivos e finitos")


def grafico_g1(dados_reais: pd.DataFrame, dados_simulados: pd.DataFrame) -> go.Figure:
    """Compara histogramas reais e simulados por grupo em escala log10."""
    _validar_dados(dados_reais, "dados_reais")
    _validar_dados(dados_simulados, "dados_simulados")

    valores_log = [
        np.log10(df["horas_ate_merge"].to_numpy(dtype=float))
        for df in (dados_reais, dados_simulados)
    ]
    limites_bins = np.histogram_bin_edges(np.concatenate(valores_log), bins=20)
    largura_bin = float(limites_bins[1] - limites_bins[0])

    figura = make_subplots(
        rows=1,
        cols=2,
        shared_yaxes=True,
        subplot_titles=[NOMES_GRUPO[grupo] for grupo in GRUPOS],
    )

    for coluna, grupo in enumerate(GRUPOS, start=1):
        cor = CORES_GRUPO[grupo]
        for df, nome, tipo_traco in (
            (dados_reais, "Reais", "histograma"),
            (dados_simulados, "Simulados", "linha"),
        ):
            valores = np.log10(
                df.loc[df["grupo"] == grupo, "horas_ate_merge"].to_numpy(dtype=float)
            )
            if tipo_traco == "histograma":
                figura.add_trace(
                    go.Histogram(
                        x=valores,
                        histnorm="probability density",
                        xbins=dict(start=float(limites_bins[0]), end=float(limites_bins[-1]), size=largura_bin),
                        name=nome,
                        legendgroup=nome,
                        marker_color=cor,
                        opacity=0.48,
                        hovertemplate="log10(horas)=%{x:.2f}<br>Densidade=%{y:.4f}<extra>%{fullData.name}</extra>",
                    ),
                    row=1,
                    col=coluna,
                )
            else:
                densidade, _ = np.histogram(valores, bins=limites_bins, density=True)
                centros = (limites_bins[:-1] + limites_bins[1:]) / 2
                figura.add_trace(
                    go.Scatter(
                        x=centros,
                        y=densidade,
                        mode="lines",
                        line=dict(color=cor, dash="dash", width=2),
                        name=nome,
                        legendgroup=nome,
                        showlegend=False,
                        hovertemplate="log10(horas)=%{x:.2f}<br>Densidade=%{y:.4f}<extra>Simulados</extra>",
                    ),
                    row=1,
                    col=coluna,
                )

        for df, nome, tracejado in (
            (dados_reais, "Mediana real", "solid"),
            (dados_simulados, "Mediana simulada", "dot"),
        ):
            mediana = float(
                df.loc[df["grupo"] == grupo, "horas_ate_merge"].median()
            )
            figura.add_vline(
                x=float(np.log10(mediana)),
                line_color=cor,
                line_dash=tracejado,
                row=1,
                col=coluna,
                annotation_text=f"{nome}: {mediana:.1f} h",
                annotation_position="top",
            )

    ticks_horas = np.array([0.01, 0.1, 1, 10, 100, 1000, 10000])
    figura.update_xaxes(
        title_text="Tempo até merge (horas; escala log10)",
        tickmode="array",
        tickvals=np.log10(ticks_horas),
        ticktext=[str(valor).replace(".", ",") for valor in ticks_horas],
    )
    figura.update_yaxes(title_text="Densidade (por unidade log10)", col=1)
    aplicar_layout(
        figura,
        title="G1 — Distribuição dos dados reais e simulados",
        barmode="overlay",
        legend_title_text="Conjunto",
    )
    return figura


def _rgba(cor: str, opacidade: float) -> str:
    rgb = tuple(int(cor[indice : indice + 2], 16) for indice in (1, 3, 5))
    return f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {opacidade})"


def _adicionar_cauda(
    figura: go.Figure,
    distribuicao,
    inicio: float,
    fim: float,
    cor: str,
    row: int = 1,
    col: int = 1,
) -> None:
    if inicio >= fim:
        return
    x = np.linspace(inicio, fim, 160)
    figura.add_trace(
        go.Scatter(
            x=x,
            y=distribuicao.pdf(x),
            mode="lines",
            line=dict(color=cor, width=0),
            fill="tozeroy",
            fillcolor=cor,
            showlegend=False,
            hoverinfo="skip",
        ),
        row=row,
        col=col,
    )


def _adicionar_areas_teste(
    figura: go.Figure,
    distribuicao,
    extensao: float,
    limite_critico: float,
    estatistica_observada: float,
    cor: str,
    row: int,
    col: int,
) -> None:
    for limite, opacidade in (
        (abs(estatistica_observada), 0.14),
        (limite_critico, 0.38),
    ):
        for inicio, fim in ((-extensao, -limite), (limite, extensao)):
            _adicionar_cauda(
                figura,
                distribuicao,
                inicio,
                fim,
                _rgba(cor, opacidade),
                row=row,
                col=col,
            )


def _escalar(resultado: Resultado, nome: str) -> float:
    valor = np.asarray(resultado, dtype=float)
    if valor.ndim != 0:
        raise ValueError(f"{nome} espera um único conjunto de dados")
    return float(valor)


def grafico_g2(sem_bot: ArrayLike, com_bot: ArrayLike) -> go.Figure:
    """Mostra as distribuições nulas, regiões críticas e áreas dos p-valores."""
    grupo_sem = np.asarray(sem_bot, dtype=float)
    grupo_com = np.asarray(com_bot, dtype=float)
    resultado_welch = teste_welch(grupo_sem, grupo_com)
    resultado_mw = teste_mann_whitney(grupo_sem, grupo_com)
    estatistica_t = _escalar(resultado_welch["estatistica"], "grafico_g2")
    p_welch = _escalar(resultado_welch["p_valor"], "grafico_g2")
    estatistica_u = _escalar(resultado_mw["estatistica"], "grafico_g2")
    p_mw = _escalar(resultado_mw["p_valor"], "grafico_g2")
    n_sem = grupo_sem.size
    n_com = grupo_com.size
    z_critico = float(stats.norm.ppf(0.975))

    variancia_sem = float(np.var(grupo_sem, ddof=1))
    variancia_com = float(np.var(grupo_com, ddof=1))
    componente_sem = variancia_sem / n_sem
    componente_com = variancia_com / n_com
    graus_liberdade = (componente_sem + componente_com) ** 2 / (
        componente_sem**2 / (n_sem - 1) + componente_com**2 / (n_com - 1)
    )
    distribuicao_t = stats.t(graus_liberdade)
    limite_t = float(stats.t.ppf(0.975, graus_liberdade))
    extensao_t = max(limite_t, abs(estatistica_t)) + 3

    figura = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=[NOMES_TESTE["welch"], NOMES_TESTE["mann_whitney"]],
    )
    grade_t = np.linspace(-extensao_t, extensao_t, 800)
    figura.add_trace(
        go.Scatter(
            x=grade_t,
            y=distribuicao_t.pdf(grade_t),
            mode="lines",
            line=dict(color=CORES_TESTE["welch"], width=2),
            name="Welch",
            hovertemplate="t=%{x:.2f}<br>Densidade=%{y:.4f}<extra>Welch</extra>",
        ),
        row=1,
        col=1,
    )
    _adicionar_areas_teste(
        figura,
        distribuicao_t,
        extensao_t,
        limite_t,
        estatistica_t,
        CORES_TESTE["welch"],
        row=1,
        col=1,
    )
    figura.add_vline(
        x=estatistica_t,
        line_color=CORES_TESTE["welch"],
        line_dash="dash",
        row=1,
        col=1,
        annotation_text=f"t observado = {estatistica_t:.2f}",
    )

    centro_u = n_sem * n_com / 2
    valores_combinados = np.concatenate((grupo_sem, grupo_com))
    _, frequencias = np.unique(valores_combinados, return_counts=True)
    n_total = n_sem + n_com
    correcao_empates = float(np.sum(frequencias**3 - frequencias))
    variancia_u = (
        n_sem
        * n_com
        / 12
        * (n_total + 1 - correcao_empates / (n_total * (n_total - 1)))
    )
    desvio_u = float(np.sqrt(max(variancia_u, 0)))
    if desvio_u > 0:
        z_observado = (
            np.sign(estatistica_u - centro_u)
            * max(abs(estatistica_u - centro_u) - 0.5, 0)
            / desvio_u
        )
        distribuicao_z = stats.norm()
        extensao_z = max(z_critico, abs(z_observado)) + 3
        grade_z = np.linspace(-extensao_z, extensao_z, 800)
        figura.add_trace(
            go.Scatter(
                x=grade_z,
                y=distribuicao_z.pdf(grade_z),
                mode="lines",
                line=dict(color=CORES_TESTE["mann_whitney"], width=2),
                name="Mann-Whitney",
                hovertemplate="z=%{x:.2f}<br>Densidade=%{y:.4f}<extra>Mann-Whitney</extra>",
            ),
            row=1,
            col=2,
        )
        _adicionar_areas_teste(
            figura,
            distribuicao_z,
            extensao_z,
            z_critico,
            z_observado,
            CORES_TESTE["mann_whitney"],
            row=1,
            col=2,
        )
        figura.add_vline(
            x=z_observado,
            line_color=CORES_TESTE["mann_whitney"],
            line_dash="dash",
            row=1,
            col=2,
            annotation_text=f"z observado = {z_observado:.2f}",
        )
    else:
        figura.add_vline(
            x=0,
            line_color=CORES_TESTE["mann_whitney"],
            line_dash="dash",
            row=1,
            col=2,
            annotation_text="Distribuição degenerada",
        )

    figura.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker=dict(symbol="square", size=12, color="rgba(90, 90, 90, 0.38)"),
            name="Região de rejeição",
        )
    )
    figura.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker=dict(symbol="square", size=12, color="rgba(90, 90, 90, 0.14)"),
            name="Área do p-valor",
        )
    )
    figura.update_xaxes(title_text="Estatística t", row=1, col=1)
    figura.update_xaxes(title_text="Estatística z do U", row=1, col=2)
    figura.update_yaxes(title_text="Densidade sob H0", row=1, col=1)
    figura.update_yaxes(title_text="Densidade sob H0", row=1, col=2)
    aplicar_layout(
        figura,
        title="G2 — Distribuições das estatísticas sob H0",
        showlegend=True,
    )
    figura.add_annotation(
        x=0,
        y=-0.22,
        xref="paper",
        yref="paper",
        text=(
            f"p de Welch = {p_welch:.4f} · p de Mann-Whitney = {p_mw:.4f}. "
            "A área clara indica o p-valor bicaudal; a região mais escura indica α = 0,05."
        ),
        showarrow=False,
        align="left",
    )
    figura.update_layout(margin=dict(b=115))
    return figura


# ------------------------------------------------------------------ G3 e G4

ORDEM_SITUACOES = ("base", "assimetria_extrema", "com_outliers", "amostra_pequena")
ROTULOS_SITUACAO = {
    "base": "Base",
    "assimetria_extrema": "Assimetria extrema (σ × 2)",
    "com_outliers": "Com outliers (5% × 10)",
    "amostra_pequena": "Amostra pequena",
}
_TESTES_ORDEM = ("welch", "mann_whitney")
_COR_FAIXA = "rgba(120, 120, 120, 0.16)"
_COR_TEXTO = "#1a1f26"


def _linhas_situacao(df: pd.DataFrame, situacao: str) -> pd.DataFrame:
    """Base vem da Q1 (erro tipo I) ou da Q2 (poder); as outras, da Q3."""
    if situacao == "base":
        return df[(df["situacao"] == "base") & (df["pergunta"].isin(["Q1", "Q2"]))]
    return df[(df["situacao"] == situacao) & (df["pergunta"] == "Q3")]


def _rotulo_com_n(df: pd.DataFrame, situacao: str) -> str:
    n = int(_linhas_situacao(df, situacao)["n_por_grupo"].iloc[0])
    return f"{ROTULOS_SITUACAO[situacao]} · n = {n}"


def grafico_g3(df: pd.DataFrame, alpha: float = 0.05) -> go.Figure:
    """Erro tipo I por situacao: ponto + IC 95% contra a linha de alpha.

    Forma "distancia ate um alvo": o que importa e quanto cada teste se afasta
    de alpha, nao o tamanho a partir do zero. A faixa cinza e o que o acaso
    de 10.000 repeticoes explica (alpha ± 1,96 EP).
    """
    figura = go.Figure()
    n_rep = int(df["n_rep"].iloc[0])
    meia_faixa = 1.96 * np.sqrt(alpha * (1 - alpha) / n_rep)
    figura.add_vrect(
        x0=alpha - meia_faixa, x1=alpha + meia_faixa, fillcolor=_COR_FAIXA, line_width=0, layer="below",
        annotation_text="faixa do acaso", annotation_position="top left",
        annotation_font=dict(size=11, color="#555"),
    )
    figura.add_vline(
        x=alpha, line_color="#555", line_dash="dash", line_width=1,
        annotation_text=f"α = {str(alpha).replace('.', ',')}", annotation_position="bottom right",
        annotation_font=dict(size=11, color="#555"),
    )
    posicoes = {s: len(ORDEM_SITUACOES) - 1 - i for i, s in enumerate(ORDEM_SITUACOES)}
    deslocamento = {"welch": 0.14, "mann_whitney": -0.14}
    maximo = alpha
    for teste in _TESTES_ORDEM:
        x, y, inf, sup, textos = [], [], [], [], []
        for situacao in ORDEM_SITUACOES:
            linhas = _linhas_situacao(df, situacao)
            if situacao == "base":
                linhas = linhas[linhas["pergunta"] == "Q1"]
            linha = linhas[(linhas["teste"] == teste) & (linhas["efeito"] == 0)].iloc[0]
            x.append(float(linha["taxa_rejeicao"]))
            inf.append(float(linha["ic95_inf"]))
            sup.append(float(linha["ic95_sup"]))
            y.append(posicoes[situacao] + deslocamento[teste])
            textos.append(ROTULOS_SITUACAO[situacao])
            maximo = max(maximo, float(linha["ic95_sup"]))
        x_arr, inf_arr, sup_arr = np.array(x), np.array(inf), np.array(sup)
        figura.add_trace(
            go.Scatter(
                x=x_arr, y=y, mode="markers", name=NOMES_TESTE[teste],
                marker=dict(color=CORES_TESTE[teste], size=11, line=dict(color="white", width=2)),
                error_x=dict(type="data", symmetric=False, array=sup_arr - x_arr,
                             arrayminus=x_arr - inf_arr, color=CORES_TESTE[teste], thickness=2, width=0),
                customdata=np.column_stack([inf_arr, sup_arr]), text=textos,
                hovertemplate=(
                    "%{text}<br>Erro tipo I = %{x:.2%}<br>IC 95%: %{customdata[0]:.2%} a "
                    "%{customdata[1]:.2%}<extra>%{fullData.name}</extra>"
                ),
            )
        )
    figura.update_yaxes(
        tickmode="array", tickvals=[posicoes[s] for s in ORDEM_SITUACOES],
        ticktext=[_rotulo_com_n(df, s) for s in ORDEM_SITUACOES],
        range=[-0.9, len(ORDEM_SITUACOES) - 0.4], showgrid=False,
    )
    figura.update_xaxes(
        title_text="Erro tipo I (proporção de rejeições com H0 verdadeira)",
        tickformat=".1%", range=[-maximo * 0.03, maximo * 1.15],
    )
    aplicar_layout(
        figura,
        title=f"G3 — Erro tipo I com H0 verdadeira (α = {str(alpha).replace('.', ',')}, 10.000 repetições)",
        height=420,
        margin=dict(l=230, r=20, t=90, b=60),
    )
    return figura


def grafico_g4(df: pd.DataFrame, alpha: float = 0.05, alvo: float = 0.80) -> go.Figure:
    """Curvas de poder, um painel por situacao, mesmo eixo Y (0 a 100%)."""
    figura = make_subplots(
        rows=2, cols=2, shared_xaxes=True, shared_yaxes=True,
        subplot_titles=[_rotulo_com_n(df, s) for s in ORDEM_SITUACOES],
        vertical_spacing=0.14, horizontal_spacing=0.06,
    )
    for indice, situacao in enumerate(ORDEM_SITUACOES):
        linha_painel, coluna_painel = divmod(indice, 2)
        linha_painel, coluna_painel = linha_painel + 1, coluna_painel + 1
        dados = _linhas_situacao(df, situacao)
        if situacao == "base":
            dados = dados[dados["pergunta"] == "Q2"]
        for teste in _TESTES_ORDEM:
            curva = dados[dados["teste"] == teste].sort_values("efeito")
            x = curva["efeito"].to_numpy(dtype=float)
            figura.add_trace(
                go.Scatter(
                    x=np.concatenate([x, x[::-1]]),
                    y=np.concatenate([curva["ic95_sup"].to_numpy(), curva["ic95_inf"].to_numpy()[::-1]]),
                    mode="none", fill="toself", fillcolor=_rgba(CORES_TESTE[teste], 0.12),
                    name=f"IC 95% {NOMES_TESTE[teste]}", showlegend=False, hoverinfo="skip",
                ),
                row=linha_painel, col=coluna_painel,
            )
            figura.add_trace(
                go.Scatter(
                    x=x, y=curva["taxa_rejeicao"], mode="lines+markers", name=NOMES_TESTE[teste],
                    legendgroup=teste, showlegend=indice == 0,
                    line=dict(color=CORES_TESTE[teste], width=2),
                    marker=dict(size=8, color=CORES_TESTE[teste], line=dict(color="white", width=2)),
                    hovertemplate=(
                        "Efeito = %{x:.1f}<br>Poder = %{y:.1%}<extra>%{fullData.name}</extra>"
                    ),
                ),
                row=linha_painel, col=coluna_painel,
            )
            if indice == 0 and len(x):
                figura.add_annotation(
                    x=x[-1], y=float(curva["taxa_rejeicao"].iloc[-1]), text=NOMES_TESTE[teste],
                    xanchor="right", yanchor="bottom", xshift=-6, showarrow=False,
                    font=dict(color=_COR_TEXTO, size=12), row=linha_painel, col=coluna_painel,
                )
        figura.add_hline(
            y=alvo, line_color="#555", line_dash="dash", line_width=1,
            row=linha_painel, col=coluna_painel,
        )
    figura.add_annotation(
        x=0, y=alvo, xref="x", yref="y", text=f"{alvo:.0%} de poder", showarrow=False,
        xanchor="left", yanchor="bottom", font=dict(size=11, color="#555"),
    )
    figura.update_yaxes(range=[0, 1], tickformat=".0%")
    figura.update_yaxes(title_text="Poder", col=1)
    figura.update_xaxes(title_text="Efeito (redução relativa da mediana)", row=2)
    aplicar_layout(
        figura,
        title=f"G4 — Poder por tamanho do efeito (α = {str(alpha).replace('.', ',')}, 10.000 repetições)",
        height=620,
    )
    return figura
