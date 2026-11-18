# LAB05 — Experimento final: DuckDB × SQLite

Experimento controlado que compara dois bancos de dados embarcados em produção, **DuckDB** (colunar, vetorizado) e **SQLite** (orientado a linhas), em carga analítica (TPC-H, 22 consultas) e transacional (leitura e escrita de uma linha), em dois tamanhos de dados (sf 0,1 e 1).

**Pergunta de pesquisa:** em consultas analíticas, quanto o DuckDB é mais rápido que o SQLite, essa vantagem vem do motor colunar ou só do paralelismo, e ela se inverte em operações transacionais?

## Tratamentos

| Tratamento | Engine | Para quê |
|---|---|---|
| `sqlite` | SQLite (via `apsw`) | linha de base, single-thread |
| `duckdb_t1` | DuckDB, 1 thread | isola o efeito do motor colunar |
| `duckdb_t4` | DuckDB, 4 threads | uso real (paralelo) |

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `infra/` | imagem Docker de benchmark (versões fixadas, limites de CPU/memória) |
| `bench/` | geração TPC-H, consultas nos 2 dialetos, OLTP, agenda sorteada e orquestrador |
| `data/` | bancos (fora do git), resultados brutos, `results.csv`, `manifest.json` |
| `analysis/` | validação, descritiva, testes de hipótese, gráficos, impacto, dashboard |
| `docs/` | planejamento, método, resultados, ameaças, impacto, relatório e apresentação |

Documentos principais: [planejamento](docs/planejamento.md) · [convenções](docs/convencoes.md) · [software e critérios](docs/01-software-criterios.md) · [GQM e hipóteses](docs/02-gqm-hipoteses.md) · [categorias](docs/03-categorias.md) · [plano de coleta e análise](docs/04-plano-coleta-analise.md).

## Ambiente

```bash
python -m venv .venv
.venv/Scripts/activate            # Windows (Git Bash); no Linux/macOS: source .venv/bin/activate
pip install -r requirements.lock
pip install -e .[dev] --no-deps
make test
```

Requer Python ≥ 3.12, Docker e `make` (no Windows: `choco install make` ou `winget install GnuWin32.Make`).

## Como reproduzir

```bash
make preflight && make data && make pilot && make run && make analyze PHASE=full && make dashboard
```

(Os alvos são implementados ao longo das sprints; ver `docs/planejamento.md`.)
