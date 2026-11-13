# Lab04 — Testes de hipótese por dentro

Laboratório de Experimentação de Software · PUC Minas · 2026/2

Compara o **t de Welch** e o **Mann-Whitney** (par P1) no cenário *"o uso de bot de revisão muda o tempo até o merge de PRs?"*. Os dados reais (PRs do [microsoft/PowerToys](https://github.com/microsoft/PowerToys) com e sem revisão do Copilot) servem para calibrar uma simulação lognormal. Com ela medimos o erro tipo I e o poder de cada teste.

- **GitHub Projects:** [Projetos do repositório](https://github.com/gabrieltinoco/Laboratorio-Experimentacao-de-Software/projects)
- **Dashboard publicado:** [abrir no Streamlit Community Cloud](https://lab04-teste-hipotese.streamlit.app/)
- Enunciado e plano de sprints: material da disciplina (Canvas)

## Instalação

Requer Python 3.12 ou superior.

```bash
cd Laboratorio04
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Comandos

```bash
python -m src.parametros           # ajuste da lognormal aos dados reais
python -m src.simulacao            # gera results/exemplo_simulado.csv (seed 42)
python -m src.experimentos         # Q1, Q2 e Q3: CSVs de resultados, seed 42
python -m src.tamanho_amostra      # poder x n com o efeito real: results/tamanho_amostra.csv
python run_all.py                  # ajusta parâmetros e gera Q1-Q3 com seed 42
python -m pytest                   # executa os testes automatizados
streamlit run dashboard/app.py     # abre o dashboard
```

O dashboard apresenta o cenário, compara os dados reais e simulados (G1), aplica
o t de Welch e Mann-Whitney ao conjunto simulado (G2), e mostra os resultados das
simulações Q1-Q3 (G3 e G4). `python run_all.py` ajusta os parâmetros usando os
dados reais versionados, cria um gerador aleatório com seed 42 e gera os arquivos
de resultados para α = 0,05 e α = 0,01. A coleta pela API do GitHub não faz parte
desse comando.

A coleta dos dados reais **não** precisa ser refeita: `data/real/prs.csv` está versionado. Para refazê-la, defina `GITHUB_TOKEN` (só leitura de repositórios públicos) e rode `python -m src.coleta`. Detalhes em [data/real/FONTE.md](data/real/FONTE.md).

## Estrutura

```
Laboratorio04/
├── README.md
├── requirements.txt
├── data/real/
│   ├── prs.csv               # 30 PRs com bot + 30 sem bot
│   └── FONTE.md              # origem, critério, limitações
├── docs/
│   ├── cenario.md            # pergunta, H0/H1, palpite, parâmetros
│   ├── resultados_simulacao.md  # números de Q1, Q2, Q3, α = 0,01 e tamanho da amostra
│   ├── roteiro_apresentacao_A.md
│   └── roteiro_apresentacao_B.md
├── results/
│   ├── exemplo_simulado.csv  # um conjunto simulado (n = 30, efeito = 0,3)
│   ├── q1_q2_q3.csv          # taxas de rejeição (α = 0,05), 10.000 repetições por ponto
│   ├── q1_q2_q3_alpha001.csv # o mesmo com α = 0,01
│   └── tamanho_amostra.csv   # poder com o efeito real para n = 30 … 1.600
├── run_all.py                # pipeline reproduzível completo (seed 42)
├── dashboard/
│   └── app.py                # dashboard Streamlit com G1, G2, G3 e G4
└── src/
    ├── coleta.py             # coleta via API do GitHub
    ├── parametros.py         # ajuste da lognormal aos dados reais
    ├── simulacao.py          # gerador de dados simulados
    ├── testes.py             # Welch e Mann-Whitney, vetorizados
    ├── experimentos.py       # motor: taxa de rejeição em 10.000 repetições
    ├── cenarios_q3.py        # situações que violam pressupostos (Q3)
    ├── dados_reais.py        # tabela dos testes nos dados reais (seção 6)
    ├── tamanho_amostra.py    # poder × n e n para 80% de poder
    ├── graficos.py           # gráficos G1, G2, G3 e G4
    └── estilo.py             # cores por teste e template Plotly
tests/
├── test_experimentos.py      # reprodutibilidade, erro tipo I e shape
├── test_graficos_g1.py       # distribuição e escala de G1
├── test_graficos_g3_g4.py    # gráficos de erro tipo I e poder
└── test_motor.py             # motor, Q3, dados reais e tamanho da amostra
```

## Convenções

- Semente fixa: `rng = np.random.default_rng(42)` só no ponto de entrada, passado como parâmetro. Nenhuma função cria seu próprio gerador.
- Cores fixas por teste em todos os gráficos (`src/estilo.py`): Welch = azul `#1f77b4`, Mann-Whitney = laranja `#ff7f0e`.
- Todo commit cita o número da issue (`#58`).
