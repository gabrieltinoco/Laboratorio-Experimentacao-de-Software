# Lab04 — Testes de hipótese por dentro

Laboratório de Experimentação de Software · PUC Minas · 2026/2

Compara o **t de Welch** e o **Mann-Whitney** (par P1) no cenário *"o uso de bot de revisão muda o tempo até o merge de PRs?"*. Os dados reais (PRs do [microsoft/PowerToys](https://github.com/microsoft/PowerToys) com e sem revisão do Copilot) servem para calibrar uma simulação lognormal. Com ela medimos o erro tipo I e o poder de cada teste.

- **GitHub Projects:** _<preencher com o link do Project do Lab04>_
- **Dashboard publicado:** _<preencher na entrega final>_
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
streamlit run dashboard/app.py     # abre o dashboard
```

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
│   └── cenario.md            # pergunta, H0/H1, palpite, parâmetros
├── results/
│   └── exemplo_simulado.csv  # um conjunto simulado (n = 30, efeito = 0,3)
└── src/
    ├── coleta.py             # coleta via API do GitHub
    ├── parametros.py         # ajuste da lognormal aos dados reais
    ├── simulacao.py          # gerador de dados simulados
    └── estilo.py             # cores por teste e template Plotly
```

## Convenções

- Semente fixa: `rng = np.random.default_rng(42)` só no ponto de entrada, passado como parâmetro. Nenhuma função cria seu próprio gerador.
- Cores fixas por teste em todos os gráficos (`src/estilo.py`): Welch = azul `#1f77b4`, Mann-Whitney = laranja `#ff7f0e`.
- Todo commit cita o número da issue (`#58`).
