"""Dashboard do Lab04: compara o t de Welch e o teste de Mann-Whitney."""

from pathlib import Path

import streamlit as st
import pandas as pd

from src.dados_reais import resumo_grupos, tabela_testes_reais
from src.estilo import NOMES_TESTE
from src.graficos import ROTULOS_SITUACAO, grafico_g1, grafico_g2, grafico_g3, grafico_g4
from src.parametros import ajustar_por_grupo, parametros_simulacao
from src.tamanho_amostra import grafico_tamanho_amostra, n_para_poder
from src.testes import teste_mann_whitney, teste_welch

RAIZ = Path(__file__).resolve().parents[1]
ARQ_CENARIO = RAIZ / "docs" / "cenario.md"
ARQ_PRS = RAIZ / "data" / "real" / "prs.csv"
ARQ_SIMULADO = RAIZ / "results" / "exemplo_simulado.csv"
ARQ_TAMANHO = RAIZ / "results" / "tamanho_amostra.csv"
ARQ_RESULTADOS = RAIZ / "results" / "q1_q2_q3.csv"
ARQ_RESULTADOS_ALPHA001 = RAIZ / "results" / "q1_q2_q3_alpha001.csv"


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

def br(valor: float, casas: int = 1) -> str:
    """Número no formato brasileiro (1.234,5)."""
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "_").replace(".", ",").replace("_", ".")


dados_reais = carregar_csv(str(ARQ_PRS))
dados_simulados = carregar_csv(str(ARQ_SIMULADO))
ajuste = ajustar_por_grupo(dados_reais)
params_sim = parametros_simulacao(dados_reais)
resumo_real = resumo_grupos(dados_reais)
n_sem = int(resumo_real.loc["sem_bot", "n"])
n_com = int(resumo_real.loc["com_bot", "n"])

st.header("1. Cenário")
st.markdown(
    f"""
**Pergunta:** o uso de um bot de revisão de código muda o tempo até o merge de pull requests?

- **H0:** o tempo até o merge tem a mesma distribuição com e sem bot ($F_{{sem}} = F_{{com}}$).
- **H1:** as distribuições diferem ($F_{{sem}} \\neq F_{{com}}$): em um dos grupos os PRs tendem
  a chegar ao merge antes. O teste é **bicaudal**, porque o bot pode acelerar o merge (aponta
  problemas cedo) ou atrasá-lo (gera mais comentários para resolver). α = 0,05.
- **Dados:** PRs com merge entre 01/08 e 31/10/2026 no repositório público
  [microsoft/PowerToys](https://github.com/microsoft/PowerToys), coletados pela API REST do GitHub.
  "Com bot" = PR revisado pelo `copilot-pull-request-reviewer[bot]`; "sem bot" = PR sem essa review.
  **{n_com} PRs com bot e {n_sem} PRs sem bot**, sorteados com semente 42 entre 483 PRs abertos
  por pessoas. Variável: `horas_ate_merge = merged_at − created_at`.
- **Par de testes:** t de Welch (compara médias) × Mann-Whitney (compara postos).
"""
)
with st.expander("Cenário completo: palpite registrado, erros tipo I e II, parâmetros"):
    st.markdown(carregar_cenario())

st.header("2. Os dados — G1")
st.plotly_chart(grafico_g1(dados_reais, dados_simulados), use_container_width=True)
st.markdown(
    f"Os tempos reais são muito assimétricos: sem bot a mediana é de "
    f"{br(resumo_real.loc['sem_bot', 'mediana'])} h e a média de "
    f"{br(resumo_real.loc['sem_bot', 'media'], 0)} h; com bot, "
    f"{br(resumo_real.loc['com_bot', 'mediana'])} h e {br(resumo_real.loc['com_bot', 'media'], 0)} h, "
    f"com outliers mantidos, como um PR que esperou "
    f"{br(resumo_real['maximo'].max(), 0)} h (~6 meses) e outro com merge em 1 minuto. "
    f"Em escala log, que é o eixo do G1, os dados ficam próximos de uma normal (assimetria de log(x) "
    f"de {br(ajuste.loc['com_bot', 'assimetria_log'], 2)} com bot e "
    f"{br(ajuste.loc['sem_bot', 'assimetria_log'], 2)} sem bot), e por isso a simulação usa uma "
    f"**lognormal**. Os parâmetros saem de `src/parametros.py`: mediana de "
    f"{br(params_sim['mediana'])} h (e^mu do grupo sem bot) e sigma de "
    f"{br(params_sim['sigma'], 2)} (média dos dois grupos), iguais nos dois grupos para que H0 "
    f"seja exatamente verdadeira com efeito 0. As linhas tracejadas (um conjunto simulado com "
    f"efeito 0,3) acompanham as barras reais, então a simulação reproduz a forma dos dados."
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

def tabela_visivel(df: pd.DataFrame) -> pd.DataFrame:
    """Versão em tabela dos gráficos G3/G4 (acessibilidade: todo valor legível sem hover)."""
    return pd.DataFrame(
        {
            "Pergunta": df["pergunta"],
            "Situação": df["situacao"].map(ROTULOS_SITUACAO),
            "Teste": df["teste"].map(NOMES_TESTE),
            "Efeito": df["efeito"],
            "n por grupo": df["n_por_grupo"],
            "Taxa de rejeição": (100 * df["taxa_rejeicao"]).round(2).astype(str) + "%",
            "IC 95%": (100 * df["ic95_inf"]).round(2).astype(str)
            + "% a "
            + (100 * df["ic95_sup"]).round(2).astype(str)
            + "%",
        }
    )


st.divider()
escolha_alpha = st.radio(
    "Nível de significância das seções 4 e 5",
    options=[0.05, 0.01],
    format_func=lambda a: f"α = {br(a, 2)}",
    horizontal=True,
    help="α = 0,01 responde à pergunta: o que muda no G3 e no G4 com um α menor?",
)
arq_resultados = ARQ_RESULTADOS if escolha_alpha == 0.05 else ARQ_RESULTADOS_ALPHA001
resultados_sim = carregar_csv(str(arq_resultados)) if arq_resultados.exists() else None

st.header("4. Erro tipo I — G3")
if resultados_sim is None:
    st.info("Rode `python -m src.experimentos` para gerar results/q1_q2_q3.csv.")
else:
    st.plotly_chart(grafico_g3(resultados_sim, alpha=escolha_alpha), use_container_width=True)
    erro_i = resultados_sim[(resultados_sim["efeito"] == 0) & (resultados_sim["pergunta"] != "Q2")]
    erro_i = erro_i.set_index(["situacao", "teste"])["taxa_rejeicao"]
    taxa_mw = erro_i.xs("mann_whitney", level="teste")
    taxa_welch_base = erro_i.loc[("base", "welch")]
    taxa_welch_assimetria = erro_i.loc[("assimetria_extrema", "welch")]
    st.markdown(
        f"Cada barra mostra a taxa de rejeição de H0 verdadeira em {br(resultados_sim['n_rep'].iloc[0], 0)} "
        f"simulações, com IC de 95%; a linha horizontal marca α = {br(escolha_alpha * 100, 0)}%. "
        f"O Mann-Whitney ficou próximo de α nas situações avaliadas "
        f"({br(100 * taxa_mw.min(), 2)}% a {br(100 * taxa_mw.max(), 2)}%). "
        f"O t de Welch foi conservador, com {br(100 * taxa_welch_base, 2)}% na situação base e "
        f"{br(100 * taxa_welch_assimetria, 2)}% sob assimetria extrema, consistente com a "
        "sensibilidade da média e da variância às caudas longas."
    )
    with st.expander("Ver os valores do G3 em tabela"):
        st.dataframe(tabela_visivel(resultados_sim[resultados_sim["efeito"] == 0]), hide_index=True)

st.header("5. Poder — G4")
if resultados_sim is not None:
    st.plotly_chart(grafico_g4(resultados_sim, alpha=escolha_alpha), use_container_width=True)
    efeito_maximo = resultados_sim["efeito"].max()
    poder_maximo = resultados_sim[
        (resultados_sim["efeito"] == efeito_maximo)
        & (resultados_sim["pergunta"] != "Q1")
    ].set_index(["situacao", "teste"])["taxa_rejeicao"]
    curvas = resultados_sim[resultados_sim["pergunta"] != "Q1"]
    comparacao_curvas = curvas.pivot_table(
        index=["situacao", "efeito"], columns="teste", values="taxa_rejeicao"
    )
    mw_superior_em_todos = (
        {"mann_whitney", "welch"}.issubset(comparacao_curvas.columns)
        and (comparacao_curvas["mann_whitney"] > comparacao_curvas["welch"]).all()
    )
    conclusao_curvas = (
        "O Mann-Whitney teve poder maior em todos os efeitos e cenários simulados; "
        "não houve inversão da vantagem."
        if mw_superior_em_todos
        else "A vantagem variou entre os cenários; compare as curvas para identificar onde cada teste teve maior poder."
    )
    st.markdown(
        f"Cada curva mostra o poder conforme aumenta a redução relativa da mediana; a faixa clara "
        f"é o IC de 95% e a linha tracejada marca 80%. No maior efeito simulado ({br(efeito_maximo * 100, 0)}%), "
        f"o poder na situação base foi {br(100 * poder_maximo.loc[('base', 'mann_whitney')], 1)}% "
        f"para Mann-Whitney e {br(100 * poder_maximo.loc[('base', 'welch')], 1)}% para Welch. "
        f"{conclusao_curvas}"
    )
    with st.expander("Ver os valores do G4 em tabela"):
        st.dataframe(tabela_visivel(resultados_sim[resultados_sim["pergunta"] != "Q1"]), hide_index=True)
else:
    st.info("Rode `python -m src.experimentos` para gerar os resultados das curvas de poder.")
st.divider()

st.header("6. Testes nos dados reais")
tabela_real = tabela_testes_reais(dados_reais)
_testes_reais = tabela_real.set_index("teste")
kpi = st.columns(4)
kpi[0].metric("Mediana sem bot", f"{br(resumo_real.loc['sem_bot', 'mediana'])} h")
kpi[1].metric(
    "Mediana com bot",
    f"{br(resumo_real.loc['com_bot', 'mediana'])} h",
    delta=f"{br(resumo_real.loc['com_bot', 'mediana'] - resumo_real.loc['sem_bot', 'mediana'])} h",
    delta_color="off",
)
kpi[2].metric("p-valor do t de Welch", br(_testes_reais.loc["welch", "p_valor"], 3))
kpi[3].metric("p-valor do Mann-Whitney", br(_testes_reais.loc["mann_whitney", "p_valor"], 3))
st.dataframe(
    pd.DataFrame(
        {
            "Teste": tabela_real["nome"],
            "Estatística": tabela_real["estatistica"].round(3),
            "p-valor": tabela_real["p_valor"].round(4),
            "Tamanho do efeito": [
                f"{medida} = {br(valor, 3)}"
                for medida, valor in zip(tabela_real["medida_efeito"], tabela_real["efeito"])
            ],
            "Conclusão (α = 0,05)": tabela_real["conclusao"],
        }
    ),
    hide_index=True,
    use_container_width=True,
)
st.dataframe(
    resumo_real.rename(
        index={"sem_bot": "Sem bot", "com_bot": "Com bot"},
        columns={
            "n": "n",
            "mediana": "Mediana (h)",
            "media": "Média (h)",
            "minimo": "Mínimo (h)",
            "maximo": "Máximo (h)",
        },
    ).round(1),
    use_container_width=True,
)
welch_real = tabela_real.set_index("teste").loc["welch"]
mw_real = tabela_real.set_index("teste").loc["mann_whitney"]
dif_mediana = resumo_real.loc["sem_bot", "mediana"] - resumo_real.loc["com_bot", "mediana"]
concordam = welch_real["conclusao"] == mw_real["conclusao"]
st.markdown(
    f"Nos {n_sem + n_com} PRs reais, o t de Welch dá t = {br(welch_real['estatistica'], 2)} "
    f"(p = {br(welch_real['p_valor'], 3)}) e o Mann-Whitney dá U = {br(mw_real['estatistica'], 0)} "
    f"(p = {br(mw_real['p_valor'], 3)}). "
    + (
        f"Os dois testes **concordam** ({welch_real['conclusao']} a 5%). "
        if concordam
        else "Os dois testes **discordam** a 5%. "
    )
    + f"A mediana com bot é {br(dif_mediana)} h menor "
    f"({br(resumo_real.loc['com_bot', 'mediana'])} h × {br(resumo_real.loc['sem_bot', 'mediana'])} h), "
    f"mas os tamanhos de efeito são pequenos (g = {br(welch_real['efeito'], 2)}, "
    f"r = {br(mw_real['efeito'], 2)}). "
    "Na prática, uns 15 h a menos num ciclo de cerca de dois dias interessariam ao time, mas com 30 "
    "PRs por grupo os dados não separam esse efeito do acaso, e parte dele pode vir do tamanho dos "
    "PRs, já que os PRs com bot são menores (limitações em `data/real/FONTE.md`)."
)

st.subheader("Extra: quantos PRs seriam precisos?")
if ARQ_TAMANHO.exists():
    tamanho = carregar_csv(str(ARQ_TAMANHO))
    efeito_real = float(tamanho["efeito"].iloc[0])
    poder_30 = tamanho[tamanho["n_por_grupo"] == 30].set_index("teste")["taxa_rejeicao"]
    n80_mw = n_para_poder(tamanho, "mann_whitney")
    n80_welch = n_para_poder(tamanho, "welch")
    n_max = int(tamanho["n_por_grupo"].max())
    st.plotly_chart(grafico_tamanho_amostra(tamanho), use_container_width=True)
    st.markdown(
        f"Simulamos 10.000 conjuntos com o efeito observado nos dados reais (redução de "
        f"{br(100 * efeito_real, 0)}% na mediana ajustada) e vários n. Com o n coletado (30 por "
        f"grupo), o poder é de só {br(100 * poder_30['mann_whitney'], 1)}% no Mann-Whitney e "
        f"{br(100 * poder_30['welch'], 1)}% no t de Welch. O \"não rejeita H0\" da tabela acima é o "
        f"esperado mesmo que o efeito seja real: **não significativo não quer dizer sem efeito**. "
        + (
            f"Para 80% de poder seriam precisos cerca de **{br(n80_mw, 0)} PRs por grupo** no "
            f"Mann-Whitney"
            if n80_mw
            else f"Nenhum dos testes chega a 80% de poder até n = {n_max}"
        )
        + (
            f", e o Welch não chega a 80% nem com {br(n_max, 0)}. "
            if n80_welch is None
            else f" e {br(n80_welch, 0)} no Welch. "
        )
        + "Com amostras desse tamanho quase qualquer diferença vira significativa, e aí o que "
        "importa é o tamanho do efeito (quantas horas o bot economiza), não o p-valor."
    )
else:
    st.info("Rode `python -m src.tamanho_amostra` para gerar results/tamanho_amostra.csv.")

st.header("7. Conclusão")
st.info("A conclusão será preenchida após a comparação das simulações.")
