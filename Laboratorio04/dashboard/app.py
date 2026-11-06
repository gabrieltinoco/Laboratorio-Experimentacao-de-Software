"""Dashboard do Lab04: compara o t de Welch e o teste de Mann-Whitney."""

from pathlib import Path

import streamlit as st
import pandas as pd

from src.graficos import grafico_g1, grafico_g2
from src.testes import teste_mann_whitney, teste_welch

RAIZ = Path(__file__).resolve().parents[1]
ARQ_CENARIO = RAIZ / "docs" / "cenario.md"
ARQ_PRS = RAIZ / "data" / "real" / "prs.csv"
ARQ_SIMULADO = RAIZ / "results" / "exemplo_simulado.csv"


@st.cache_data
def carregar_csv(caminho: str) -> pd.DataFrame:
    return pd.read_csv(caminho)


@st.cache_data
def carregar_cenario() -> str:
    return ARQ_CENARIO.read_text(encoding="utf-8")


st.set_page_config(page_title="Lab04 — Testes de hipótese", layout="wide")

st.title("Testes de hipótese por dentro")
st.markdown(
    "**Dashboard:** [abrir local](http://localhost:8501) · "
    "**Repositório:** "
    "[Laboratorio-Experimentacao-de-Software]"
    "(https://github.com/gabrieltinoco/Laboratorio-Experimentacao-de-Software) · "
    "[GitHub Projects]"
    "(https://github.com/gabrieltinoco/Laboratorio-Experimentacao-de-Software/projects)"
)

st.header("1. Cenário")
st.markdown(carregar_cenario())

st.header("2. Os dados — G1")
dados_reais = carregar_csv(str(ARQ_PRS))
dados_simulados = carregar_csv(str(ARQ_SIMULADO))
st.plotly_chart(grafico_g1(dados_reais, dados_simulados), use_container_width=True)
st.markdown(
    "As barras mostram os tempos reais e a linha tracejada, os simulados, em cada grupo. "
    "O eixo horizontal usa escala log10 para tornar visível a cauda longa; os outliers reais "
    "foram mantidos. Como os tempos são positivos e assimétricos à direita, a simulação "
    "lognormal foi calibrada com os dados reais; os parâmetros e as limitações estão na seção 1."
)

st.header("3. Como os testes funcionam — G2")
sim_sem_bot = dados_simulados.loc[
    dados_simulados["grupo"] == "sem_bot", "horas_ate_merge"
].to_numpy(dtype=float)
sim_com_bot = dados_simulados.loc[
    dados_simulados["grupo"] == "com_bot", "horas_ate_merge"
].to_numpy(dtype=float)
resultado_welch = teste_welch(sim_sem_bot, sim_com_bot)
resultado_mw = teste_mann_whitney(sim_sem_bot, sim_com_bot)
st.plotly_chart(
    grafico_g2(sim_sem_bot, sim_com_bot),
    use_container_width=True,
)
st.markdown(
    "O t de Welch compara as médias sem exigir variâncias iguais; Mann-Whitney compara "
    "os postos e indica se um grupo tende a ter valores maiores. O G2 usa a t de "
    "Welch-Satterthwaite e a aproximação normal para z de U; a área clara é o p-valor "
    "bicaudal e a região escura indica rejeição para α = 0,05. "
    "O p-valor é calculado supondo H0 verdadeira; não é a probabilidade de H0 ser verdadeira. "
    "O efeito de Welch é Hedges' g (média sem bot menos média com bot); "
    "o r bisserial de Mann-Whitney usa a convenção do projeto, r = 1 − 2U/(n₁·n₂)."
)

st.subheader("Aplicação ao conjunto simulado")
resultados = [
    ("t de Welch (Hedges' g)", resultado_welch),
    ("Mann-Whitney (r bisserial)", resultado_mw),
]
st.dataframe(
    pd.DataFrame(
        [
            {
                "Teste": nome,
                "Estatística": resultado["estatistica"],
                "p-valor": resultado["p_valor"],
                "Tamanho do efeito": resultado["efeito"],
            }
            for nome, resultado in resultados
        ]
    ),
    hide_index=True,
    use_container_width=True,
)
for nome, resultado in resultados:
    if resultado["p_valor"] < 0.05:
        st.write(
            f"{nome}: estatística = {resultado['estatistica']:.3f}, "
            f"p = {resultado['p_valor']:.4f}, efeito = {resultado['efeito']:.3f}. "
            "Rejeitamos H0 a 5%; há evidência de diferença no tempo de merge neste "
            "conjunto simulado."
        )
    else:
        st.write(
            f"{nome}: estatística = {resultado['estatistica']:.3f}, "
            f"p = {resultado['p_valor']:.4f}, efeito = {resultado['efeito']:.3f}. "
            "Não rejeitamos H0 a 5%; este conjunto não fornece evidência suficiente de "
            "diferença no tempo de merge."
        )

st.header("4. Erro tipo I — G3")
st.info("Esta análise será desenvolvida na Sprint 2.")

st.header("5. Poder — G4")
st.info("Esta análise será desenvolvida na Sprint 2.")

st.header("6. Testes nos dados reais")
st.info("Os resultados dos testes nos dados reais serão integrados pelo responsável pela coleta.")

st.header("7. Conclusão")
st.info("A conclusão será preenchida após a comparação das simulações.")
