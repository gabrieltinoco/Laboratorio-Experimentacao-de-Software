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

    def _mediana(df: pd.DataFrame, grupo: str) -> float:
        return float(df.loc[df["grupo"] == grupo, "horas_ate_merge"].median())

    def _h(valor: float) -> str:
        return f"{valor:.1f}".replace(".", ",") + " h"

    # As medianas vao no titulo de cada painel (e nao como anotacoes nas linhas
    # verticais, que ficavam empilhadas umas sobre as outras e sobre o titulo).
    figura = make_subplots(
        rows=1,
        cols=2,
        shared_yaxes=True,
        subplot_titles=[
            f"{NOMES_GRUPO[grupo]}<br><sup>mediana real {_h(_mediana(dados_reais, grupo))} · "
            f"simulada {_h(_mediana(dados_simulados, grupo))}</sup>"
            for grupo in GRUPOS
        ],
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
                        xbins=dict(start=float(limites_bins[0]), end=float(limites_bins[-1]), size=largura_bin),
                        name=f"{nome} · {NOMES_GRUPO[grupo]}",
                        showlegend=False,
                        marker_color=cor,
                        opacity=0.48,
                        hovertemplate="log10(horas)=%{x:.2f}<br>Frequência=%{y:.0f}<extra>%{fullData.name}</extra>",
                    ),
                    row=1,
                    col=coluna,
                )
            else:
                frequencias, _ = np.histogram(valores, bins=limites_bins)
                centros = (limites_bins[:-1] + limites_bins[1:]) / 2
                figura.add_trace(
                    go.Scatter(
                        x=centros,
                        y=frequencias,
                        mode="lines",
                        line=dict(color=cor, dash="dash", width=2),
                        name=f"{nome} · {NOMES_GRUPO[grupo]}",
                        showlegend=False,
                        hovertemplate="log10(horas)=%{x:.2f}<br>Frequência=%{y:.0f}<extra>Simulados</extra>",
                    ),
                    row=1,
                    col=coluna,
                )

        for df, tracejado in ((dados_reais, "solid"), (dados_simulados, "dot")):
            figura.add_vline(
                x=float(np.log10(_mediana(df, grupo))),
                line_color=cor,
                line_dash=tracejado,
                row=1,
                col=coluna,
            )

    # Legenda neutra: explica a codificacao (barra, tracejado, linhas de mediana);
    # a cor de cada grupo ja aparece no titulo do painel.
    for nome, estilo_traco in (
        ("Reais (barras)", dict(mode="markers", marker=dict(symbol="square", size=12, color="rgba(138,143,150,0.6)"))),
        ("Simulados (tracejado)", dict(mode="lines", line=dict(color="#8a8f96", dash="dash", width=2))),
        ("Mediana real", dict(mode="lines", line=dict(color="#8a8f96", width=2))),
        ("Mediana simulada", dict(mode="lines", line=dict(color="#8a8f96", dash="dot", width=2))),
    ):
        figura.add_trace(go.Scatter(x=[None], y=[None], name=nome, hoverinfo="skip", **estilo_traco))

    ticks_horas = np.array([0.01, 0.1, 1, 10, 100, 1000, 10000])
    figura.update_xaxes(
        tickmode="array",
        tickvals=np.log10(ticks_horas),
        ticktext=[str(valor).replace(".", ",") for valor in ticks_horas],
    )
    # Um unico titulo de eixo X: os dois iguais se encostavam em telas estreitas.
    figura.update_xaxes(title_text="Tempo até merge (horas; escala log10)", col=1)
    figura.update_yaxes(title_text="Frequência (PRs por intervalo)", col=1)
    aplicar_layout(
        figura,
        title="G1 — Distribuição dos dados reais e simulados",
        barmode="overlay",
        height=480,
        margin=dict(t=110),
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
        subplot_titles=[
            f"{NOMES_TESTE['welch']} · p = {p_welch:.3f}".replace(".", ","),
            f"{NOMES_TESTE['mann_whitney']} · p = {p_mw:.3f}".replace(".", ","),
        ],
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
        annotation_text=f"t observado = {estatistica_t:.2f}".replace(".", ","),
        annotation_position="top right",
        annotation_font=dict(size=12),
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
            annotation_text=f"z observado = {z_observado:.2f}".replace(".", ","),
            annotation_position="top right",
                annotation_font=dict(size=12),
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
        height=460,
    )
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
# Titulos curtos dos paineis do G4: na largura de celular os rotulos longos
# de dois paineis vizinhos se encostavam.
_ROTULOS_CURTOS = {
    "base": "Base",
    "assimetria_extrema": "Assimetria σ×2",
    "com_outliers": "Outliers 5%×10",
    "amostra_pequena": "Amostra pequena",
}


def _linhas_situacao(df: pd.DataFrame, situacao: str) -> pd.DataFrame:
    """Base vem da Q1 (erro tipo I) ou da Q2 (poder); as outras, da Q3."""
    if situacao == "base":
        return df[(df["situacao"] == "base") & (df["pergunta"].isin(["Q1", "Q2"]))]
    return df[(df["situacao"] == situacao) & (df["pergunta"] == "Q3")]


def _rotulo_com_n(df: pd.DataFrame, situacao: str) -> str:
    n = int(_linhas_situacao(df, situacao)["n_por_grupo"].iloc[0])
    return f"{ROTULOS_SITUACAO[situacao]} · n = {n}"


def grafico_g3(df: pd.DataFrame, alpha: float = 0.05) -> go.Figure:
    """Compara o erro tipo I por situação com barras agrupadas e IC 95%."""
    figura = go.Figure()
    n_rep_valores = df["n_rep"].dropna().unique()
    if len(n_rep_valores) != 1:
        raise ValueError("G3 espera um único número de repetições por arquivo")
    n_rep = int(n_rep_valores[0])
    meia_faixa = 1.96 * np.sqrt(alpha * (1 - alpha) / n_rep)
    figura.add_hrect(
        y0=max(0, alpha - meia_faixa),
        y1=min(1, alpha + meia_faixa),
        fillcolor=_COR_FAIXA,
        line_width=0,
        layer="below",
        annotation_text="faixa do acaso",
        annotation_position="top left",
        annotation_font=dict(size=11, color="#8a8f96"),
    )
    figura.add_hline(
        y=alpha,
        line_color="#8a8f96",
        line_dash="dash",
        line_width=1,
        annotation_text=f"α = {alpha:.0%}",
        annotation_position="bottom right",
        annotation_font=dict(size=11, color="#8a8f96"),
    )
    situacoes = [
        s for s in ORDEM_SITUACOES
        if not _linhas_situacao(df, s).empty
    ]
    rotulos = [_rotulo_com_n(df, s) for s in situacoes]
    maximo = alpha + meia_faixa
    for teste in _TESTES_ORDEM:
        valores, inf, sup = [], [], []
        for situacao in situacoes:
            linhas = _linhas_situacao(df, situacao)
            if situacao == "base":
                linhas = linhas[linhas["pergunta"] == "Q1"]
            linhas_teste = linhas[(linhas["teste"] == teste) & (linhas["efeito"] == 0)]
            if len(linhas_teste) != 1:
                raise ValueError(
                    f"esperado um resultado Q1 para teste={teste}, situação={situacao}"
                )
            linha = linhas_teste.iloc[0]
            valores.append(float(linha["taxa_rejeicao"]))
            inf.append(float(linha["ic95_inf"]))
            sup.append(float(linha["ic95_sup"]))
            maximo = max(maximo, float(linha["ic95_sup"]))
        valores_arr, inf_arr, sup_arr = np.array(valores), np.array(inf), np.array(sup)
        figura.add_bar(
            x=rotulos,
            y=valores_arr,
            name=NOMES_TESTE[teste],
            marker_color=CORES_TESTE[teste],
            offsetgroup=teste,
            legendgroup=teste,
            error_y=dict(
                type="data",
                symmetric=False,
                array=sup_arr - valores_arr,
                arrayminus=valores_arr - inf_arr,
                color=CORES_TESTE[teste],
                thickness=1.5,
                width=4,
            ),
            customdata=np.column_stack([inf_arr, sup_arr]),
            hovertemplate=(
                "%{x}<br>Erro tipo I = %{y:.2%}<br>IC 95%: "
                "%{customdata[0]:.2%} a %{customdata[1]:.2%}"
                "<extra>%{fullData.name}</extra>"
            ),
        )
    figura.update_xaxes(title_text="Situação simulada")
    figura.update_yaxes(
        title_text="Erro tipo I (%)",
        tickformat=".0%",
        range=[0, min(1, maximo * 1.15)],
    )
    figura.update_xaxes(
        categoryorder="array",
        categoryarray=rotulos,
    )
    n_rep_rotulo = f"{n_rep:,}".replace(",", ".")
    aplicar_layout(
        figura,
        title=(
            "G3 — Erro tipo I com H0 verdadeira"
            f"<br><sup>α = {str(alpha).replace('.', ',')} · {n_rep_rotulo} repetições por situação</sup>"
        ),
        height=480,
        barmode="group",
        legend_title_text="Teste",
        margin=dict(l=75, r=20, t=100, b=130),
    )
    return figura


def grafico_g4(df: pd.DataFrame, alpha: float = 0.05, alvo: float = 0.80) -> go.Figure:
    """Curvas de poder, um painel por situacao, mesmo eixo Y (0 a 100%)."""
    figura = make_subplots(
        rows=2, cols=2, shared_xaxes=True, shared_yaxes=True,
        subplot_titles=[
            f"{_ROTULOS_CURTOS[s]} · n = {int(_linhas_situacao(df, s)['n_por_grupo'].iloc[0])}"
            for s in ORDEM_SITUACOES
        ],
        vertical_spacing=0.14, horizontal_spacing=0.06,
    )
    figura.update_annotations(font_size=13)  # so os titulos dos paineis existem aqui
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
                    # a esquerda do ultimo ponto: acima dele invadia o titulo do painel
                    xanchor="right", yanchor="middle", xshift=-10, showarrow=False,
                    font=dict(size=12), row=linha_painel, col=coluna_painel,
                )
        figura.add_hline(
            y=alvo, line_color="#8a8f96", line_dash="dash", line_width=1,
            row=linha_painel, col=coluna_painel,
        )
    figura.add_annotation(
        x=0, y=alvo, xref="x", yref="y", text=f"{alvo:.0%} de poder", showarrow=False,
        xanchor="left", yanchor="bottom", font=dict(size=11, color="#8a8f96"),
    )
    figura.update_yaxes(range=[0, 1], tickformat=".0%")
    figura.update_yaxes(title_text="Poder", col=1)
    figura.update_xaxes(title_text="Efeito (redução relativa da mediana)", row=2, col=1)
    aplicar_layout(
        figura,
        title=(
            "G4 — Poder por tamanho do efeito"
            f"<br><sup>α = {str(alpha).replace('.', ',')} · 10.000 repetições por ponto</sup>"
        ),
        height=700,
        margin=dict(t=110),
    )
    return figura
