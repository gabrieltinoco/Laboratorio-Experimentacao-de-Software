# LAB05 — Experimento Final: DuckDB × SQLite — Planejamento (2 integrantes)

> **Como usar:** cada tarefa tem um código (`A-1.1`, `B-2.3`…) e passos em checkbox (`- [ ]`). Execute só as tarefas do seu integrante e da sprint atual e marque os checkboxes conforme concluir. **Todo commit é feito pelo próprio integrante, com a própria conta git.**

**Objetivo:** planejar, executar e analisar um experimento controlado sobre dois bancos de dados embarcados reais, em operação e de alto impacto, e responder: *"o que o estudo mostrou?"* e *"o que isso significa para quem usa esse software?"*.

**Software:** **DuckDB** (banco analítico embarcado, colunar e vetorizado) × **SQLite** (banco embarcado orientado a linhas, presente em celulares, navegadores e sistemas operacionais). Os dois rodam no ambiente do grupo, nas versões estáveis usadas em produção. É o caminho *"Rodar o software no ambiente do grupo"*, combinado com dados públicos de adoção para estimar o impacto (Sprint 3).
> ⚠️ Cada grupo precisa de um software diferente. Na S01 o Integrante A confirma com o professor. Se outro grupo já tiver pegado, o plano reserva é *Nginx gzip × brotli × zstd*: mudam `bench/config.yaml`, `infra/`, `bench/workloads/` e o runner. O CSV, a análise e as sprints continuam iguais.

**Pergunta de pesquisa:** *Em consultas analíticas, quanto o DuckDB é mais rápido que o SQLite, essa vantagem vem do motor colunar ou só do paralelismo, e ela se inverte em operações transacionais (leitura e escrita de uma linha)?*

**Arquitetura:** o repositório tem 4 camadas desacopladas por arquivos:
- `infra/`: imagem Docker de benchmark com versões fixadas e limites de CPU/memória.
- `bench/`: gera os dados TPC-H, carrega nos dois bancos, guarda as consultas nos dois dialetos e tem o orquestrador que sorteia a ordem dos blocos e grava o JSON bruto.
- `data/`: bancos regeneráveis (fora do git), resultados brutos imutáveis, `results.csv` processado e `manifest.json` com SHA-256.
- `analysis/`: pacote Python testado com validação, descritiva, testes de hipótese, tamanho de efeito, gráficos, impacto e dashboard Streamlit.

Cada camada só lê a saída da anterior. É isso que permite o Integrante A sempre trabalhar antes do B.

**Tech stack:** Python 3.12, `duckdb` (com as extensões `tpch` e `sqlite`), `apsw` (traz o SQLite embutido numa versão fixa), Docker, `pandas`, `scipy`, `numpy`, `matplotlib`, `pyyaml`, `psutil`, `streamlit`, `pytest`, `make`, GitHub + GitHub Projects (Kanban, reuso do Lab01).

**Enunciado:** enunciado do *Laboratório 05 — Experimento em Software Real* (Prof. Danilo Maia, LES 2026/2). Salve uma cópia em `docs/enunciado-lab05.md` na tarefa A-1.1.

---

## Regra de ouro da divisão

**Em toda sprint, tudo do Integrante A pode ser feito antes de o Integrante B começar.** As tarefas de A dependem só de sprints anteriores. As de B dependem de A da mesma sprint e das anteriores. A nunca espera B dentro de uma sprint.

```
Sprint 1:  A (método + arquitetura)          ──► B (dados, consultas, orquestrador, piloto)
Sprint 2:  A (código de análise + ameaças)   ──► B (coleta completa + resultados)
Sprint 3:  A (impacto + categorias finais)   ──► B (conclusões + dashboard + rascunhos)
Final:     A (documento final + defesa)      ──► B (apresentação + ensaio + entrega)
```

| Integrante | Papel | Cobre os papéis do enunciado |
|---|---|---|
| **A** | Planejamento, Método e Impacto | Papel A (software, critérios, categorias, GQM, hipóteses, ameaças) + metade do C (código de análise, impacto) |
| **B** | Instrumentação, Operação e Comunicação | Papel B (ambiente, scripts, execução, ética, validação) + metade do C (rodar a análise, visualizações, dashboard) + apresentação |

> O professor pode pedir que **qualquer** integrante explique **qualquer** parte. Por isso existe o `docs/guia-defesa.md` (A-F.2), e cada um lê os entregáveis do outro no início da sprint seguinte.

---

## Restrições globais

- Não usar repositórios públicos do GitHub como objeto de pesquisa (mineração de commits/issues/PRs ou análise de código-fonte). O objeto é o **software em funcionamento**: DuckDB e SQLite executando consultas.
- Carga **apenas no ambiente do grupo**. Nenhum sistema de terceiros é medido.
- Não coletar dados pessoais. O TPC-H é sintético.
- Cada número de impacto ou critério tem **link + data de acesso**.
- Usar versões estáveis mantidas, fixadas no `requirements.lock`. Registrar `duckdb.__version__` e `apsw.sqlitelibversion()` em cada run.
- Apresentação de **10 minutos**. Documento e apresentação em formato livre.
- Pontuação: S01 = 5, S02 = 5, S03 = 5, Final = 5 (total 20).
- Classificar o estudo nas **7 categorias** (natureza, objetivos, abordagem, procedimentos, tempo, controle, nível de evidência), cada uma com justificativa.
- Ameaças à validade dos **4 tipos** (conclusão, interna, construto, externa), cada uma com mitigação.
- A análise respeita a **escala** de cada métrica.
- **Commits só dos integrantes:** cada integrante faz `git add`/`git commit`/`git push` com a própria conta, ao fim de cada tarefa. Mensagem: `tipo(escopo): descrição`, sem trailers de coautoria (`Co-Authored-By`). O autor de todo commit é um dos dois integrantes.
- Os bancos gerados (`data/db/`) **não** vão para o git (`.gitignore`). São regenerados de forma determinística por `make data`, e o manifest guarda os hashes.

## Pontos de atenção (casos que os testes precisam cobrir)

1. **Consulta traduzida errada para SQLite** (o dialeto muda datas, `interval`, `extract`, `substring`): sem checagem, a comparação mede consultas diferentes. Toda consulta precisa ter o mesmo `result_hash` nos dois bancos. Teste: `test_results_match_across_engines[q01..q22]` (B-1.2).
2. **Timeout do SQLite tratado como dado faltante:** consultas lentas que estouram o limite somem da análise e o SQLite parece melhor do que é. O timeout vira `elapsed_ms = timeout_ms` com `timeout=True` (dado censurado, que torna o teste conservador) e é contado e relatado. Teste: `test_validate_counts_timeouts` (B-1.4) e `test_compare_with_censored` (A-2.2).
3. **Coleta interrompida e retomada duplicando runs:** `--resume` pula blocos com JSON completo e não duplica linhas. Teste: `test_resume_skips_done_blocks` (B-1.3).
4. **Máquina sem recursos suficientes:** o preflight aborta se faltarem núcleos (< `limits.cpus`), RAM (< `limits.mem_gb` + 2) ou disco livre (< 10 GB). Teste: `test_preflight_rejects_small_host` (B-1.3).
5. **Deriva térmica/efeito de ordem e cache quente × frio:** a ordem dos blocos é sorteada, todo bloco roda em processo novo com a mesma rotina de aquecimento, e a validação faz um teste de tendência (Spearman entre `order` e `elapsed_ms` por célula, alerta se |ρ| > 0,3 com p < 0,05). Teste: `test_validate_warns_on_trend` (B-1.4).

---

## Arquitetura do repositório (fixa para o projeto inteiro)

```
lab05-duckdb-sqlite/
├── README.md                      # visão geral + como reproduzir
├── Makefile                       # preflight | data | pilot | run | validate | analyze | dashboard | test
├── pyproject.toml
├── requirements.lock              # versões exatas (duckdb, apsw, …)
├── .gitignore                     # data/db/
├── docs/
│   ├── enunciado-lab05.md
│   ├── convencoes.md              # regras do projeto (A-1.1)
│   ├── planejamento.md            # ESTE PLANO
│   ├── 01-software-criterios.md
│   ├── 02-gqm-hipoteses.md
│   ├── 03-categorias.md           # v1 (S01) e v2 (S03)
│   ├── 04-plano-coleta-analise.md
│   ├── 05-piloto.md
│   ├── 06-ameacas.md
│   ├── 07-resultados.md           # parte gerada + interpretação
│   ├── 08-impacto.md
│   ├── 09-conclusoes.md
│   ├── 10-reaproveitamento.md
│   ├── guia-defesa.md
│   ├── impacto/fontes.yaml
│   ├── evidencias/                # prints AAAA-MM-DD-<id>.png
│   ├── relatorio/relatorio.md
│   └── apresentacao/{roteiro.md, slides.*}
├── infra/
│   └── Dockerfile                 # python:3.12-slim + requirements.lock
├── bench/
│   ├── __init__.py
│   ├── config.yaml                # matriz experimental (schema abaixo)
│   ├── datagen.py                 # gera TPC-H e carrega nos 2 bancos
│   ├── queries/
│   │   ├── duckdb/q01.sql … q22.sql
│   │   └── sqlite/q01.sql … q22.sql
│   ├── oltp.py                    # point_select | insert | update
│   ├── result_hash.py             # hash canônico do resultado
│   ├── schedule.py                # Block + build_schedule
│   ├── runner.py                  # roda 1 bloco DENTRO do container → JSON
│   ├── run_matrix.py              # CLI no host: orquestra blocos via docker
│   └── env_snapshot.py
├── data/
│   ├── db/                        # tpch_sf{sf}.duckdb, tpch_sf{sf}.sqlite (gitignored)
│   ├── raw/<phase>/<block_id>.json
│   ├── raw/env.json
│   ├── processed/results.csv
│   └── manifest.json
├── analysis/
│   ├── lab05/
│   │   ├── __init__.py
│   │   ├── load.py
│   │   ├── validate.py
│   │   ├── descriptive.py
│   │   ├── stats_tests.py
│   │   ├── power.py
│   │   ├── plots.py
│   │   ├── impact.py
│   │   └── report.py
│   ├── figures/
│   └── dashboard/app.py
├── tests/
│   ├── fixtures/results_small.csv
│   ├── test_datagen.py
│   ├── test_queries.py
│   ├── test_result_hash.py
│   ├── test_oltp.py
│   ├── test_schedule.py
│   ├── test_run_matrix.py
│   ├── test_validate.py
│   ├── test_descriptive.py
│   ├── test_stats_tests.py
│   ├── test_power.py
│   └── test_impact.py
└── scripts/kanban_seed.sh
```

### Contratos de dados (todas as tarefas obedecem)

**`bench/config.yaml`**
```yaml
experiment_id: lab05-duckdb-sqlite
seed: 20262
engines:                    # 3 tratamentos
  sqlite:    { kind: sqlite }                 # single-thread por natureza
  duckdb_t1: { kind: duckdb, threads: 1 }     # isola o efeito do motor colunar
  duckdb_t4: { kind: duckdb, threads: 4 }     # uso real (paralelo)
scale_factors: [0.1, 1]     # ~100 MB e ~1 GB de dados
workloads:
  olap: { queries: [q01, q02, …, q22] }      # TPC-H completo
  oltp: { ops: [point_select, insert, update], n_ops: 2000 }
sqlite_settings:            # configuração comum de produção
  journal_mode: WAL
  synchronous: NORMAL
  cache_size_kib: 262144    # 256 MiB, igual ao memory_limit relativo do DuckDB
  indexes: true             # PKs + índices nas FKs do TPC-H (lista em datagen.py)
duckdb_settings:
  memory_limit: "4GB"
timeout_ms: 120000          # por consulta
censored_queries: []        # preenchido após o piloto (ver B-1.4)
limits: { cpus: 4, mem_gb: 8 }
repetitions: { pilot: 3, full: 10 }   # rodadas (blocos) por (engine, sf, workload)
reps_censored_full: 3       # rodadas para consultas em censored_queries
```

**Unidade de execução = bloco** `(engine, sf, workload, round)`. Cada bloco roda num **container novo**. Primeiro faz o aquecimento (`SELECT count(*)` em cada tabela, sem medir) e depois executa as consultas/operações do workload **em ordem sorteada**, cada uma uma vez. A ordem dos blocos também é sorteada.

**`data/processed/results.csv`**: uma linha por consulta/operação medida, nesta ordem:
`run_id, block_id, phase, order, timestamp_utc, engine, engine_version, sf, workload, item, round, elapsed_ms, ops_sec, p99_ms, rows_returned, result_hash, peak_rss_mb, timeout, error, valid, host_id`
- `block_id = f"{phase}-{engine}-sf{sf}-{workload}-r{round:02d}"`. `run_id = f"{block_id}-{item}"`
- `item` ∈ `q01..q22` (olap) ou `point_select|insert|update` (oltp)
- olap: `elapsed_ms` medido; `ops_sec`/`p99_ms` = NaN. oltp: `elapsed_ms` = tempo total das `n_ops`; `ops_sec`, `p99_ms` preenchidos
- Escalas: `elapsed_ms`, `ops_sec`, `p99_ms`, `peak_rss_mb`, `rows_returned` → **razão**; `engine`, `workload`, `item` → **nominal**; `sf` → razão, tratado como fator de 2 níveis

**Design experimental:** 3 tratamentos (`engine`) × 2 `sf` × itens (22 consultas + 3 operações). Repetição = rodada. Medidas repetidas por item (o mesmo item é medido em todos os tratamentos), o que permite análise **pareada por consulta**.

**Plano estatístico (fixo):**
1. **Por item** (célula `sf × item`), três comparações:
   - **C1** sqlite × duckdb_t4 (principal);
   - **C2** sqlite × duckdb_t1 (efeito do motor colunar);
   - **C3** duckdb_t1 × duckdb_t4 (efeito do paralelismo).

   Aplicar Shapiro-Wilk em `log(elapsed_ms)` nos dois grupos. Se ambos tiverem p ≥ 0,05, usar t de Welch em `log`; senão, Mann-Whitney U bilateral. Aplicar Holm dentro de cada família (C1, C2 ou C3, por `sf`), com α = 0,05. O efeito é medido por Cliff's δ (limiares de Romano: 0,147 / 0,33 / 0,474) e por **speedup** = mediana(a) / mediana(b), com IC 95% por bootstrap (5000 reamostragens, `seed`).
2. **Entre consultas** (H principal, por `sf`): **média geométrica do speedup** nas 22 consultas, com IC 95% por bootstrap sobre as consultas, mais **Wilcoxon signed-rank** pareado nas medianas por consulta (n = 22).
3. **OLTP:** o mesmo procedimento do item 1 para `ops_sec` e `p99_ms`.

---

# SPRINT 1 — Proposta + piloto (5 pts)

## Integrante A — Sprint 1

### Tarefa A-1.1: Repositório, convenções, config e Kanban

**Files:**
- Create: `README.md`, `docs/convencoes.md`, `docs/planejamento.md` (este arquivo), `pyproject.toml`, `requirements.lock`, `.gitignore`, `Makefile` (alvos de B com `@echo TODO`), `docs/enunciado-lab05.md`, `scripts/kanban_seed.sh`, a árvore de pastas (com `.gitkeep`)
- Create: `bench/config.yaml` (exatamente o schema acima)

**Interfaces:**
- Produces: `bench/config.yaml` e os alvos `make test|preflight|data|pilot|run|validate|analyze|dashboard`.

- [x] **Passo 1:** criar o repo no GitHub, clonar e criar a árvore.
- [x] **Passo 2:** `pyproject.toml` (Python ≥ 3.12; deps `duckdb apsw pandas scipy numpy matplotlib pyyaml psutil streamlit`; dev `pytest`). Gerar `requirements.lock` com `pip freeze` após instalar as versões estáveis mais recentes.
- [x] **Passo 3:** `docs/convencoes.md` com: (1) "o planejamento oficial é `docs/planejamento.md`"; (2) as Restrições globais; (3) "nunca edite `data/raw/`"; (4) "TDD com pytest; rode `make test` antes de cada commit"; (5) "cada integrante executa só as suas tarefas e marca os checkboxes"; (6) a convenção de commits.
- [ ] **Passo 4:** `scripts/kanban_seed.sh`: cria as labels `integrante-A`, `integrante-B`, `sprint-1..3`, `sprint-final`, `doc`, `codigo`, `dados` e uma issue por card da seção **Kanban** (`gh issue create`). Criar o GitHub Project com as colunas *Backlog → Sprint atual → Em andamento → Revisão → Concluído* e colocar o link na seção 7 do enunciado.
- [x] **Passo 5:** `pip install -e .[dev] && pytest` → "no tests ran" sem erro.
- [ ] **Passo 6:** **(integrante)** commit `chore: estrutura do repositório, config e kanban`.

### Tarefa A-1.2: Software e comprovação dos 3 critérios

**Files:** Create: `docs/01-software-criterios.md`, `docs/impacto/fontes.yaml`, `docs/evidencias/*.png`

**Interfaces:**
- Produces: `docs/impacto/fontes.yaml`, lista de `{id, descricao, valor, unidade, url, acessado_em: AAAA-MM-DD, criterio: real|operacao|impacto, software: duckdb|sqlite}`. Consumido por A-3.1.

- [x] **Passo 1:** tabela *Critério | Evidência | Fonte | Data* **para cada um dos dois softwares**:
  - **Real:** site oficial, documentação, organização mantenedora (DuckDB Foundation/DuckDB Labs; SQLite Consortium).
  - **Em operação:** versão atual, data do último release, política de suporte, empresas e produtos que usam em produção.
  - **Alto impacto:** para o SQLite, a página oficial sobre implantação e uso e a presença em Android, iOS e navegadores. Para o DuckDB, downloads no PyPI (pypistats), ranking no DB-Engines e uso no Stack Overflow Developer Survey.
- [x] **Passo 2:** registrar as versões escolhidas (as mesmas do `requirements.lock`) e o motivo.
- [ ] **Passo 3:** confirmar com o professor que nenhum outro grupo pegou o software. Registrar a resposta no doc.
- [ ] **Passo 4:** **(integrante)** commit `docs: software e evidências dos 3 critérios`.

### Tarefa A-1.3: GQM, hipóteses, variáveis e design

**Files:** Create: `docs/02-gqm-hipoteses.md`

- [x] **Passo 1:** objetivo no template de Basili: *Analisar* DuckDB e SQLite *com o propósito de* comparar *com respeito ao* tempo de resposta e à vazão *do ponto de vista de* desenvolvedores e analistas de dados que escolhem um banco embarcado *no contexto de* um único computador, com cargas analíticas (TPC-H) e transacionais, em 2 tamanhos de dados.
- [x] **Passo 2:** perguntas e métricas:
  - Q1: tempo das consultas analíticas → `elapsed_ms`;
  - Q2: o ganho vem do colunar ou do paralelismo? → C2 × C3;
  - Q3: o ganho cresce com o volume? → speedup por `sf`;
  - Q4: desempenho transacional → `ops_sec`, `p99_ms`;
  - Q5: custo de memória → `peak_rss_mb`.

  Para cada métrica, registrar: entidade (produto), atributo (externo), se é direta ou derivada (speedup é derivada), **escala** e estatísticas permitidas.
- [x] **Passo 3:** hipóteses:
  - H0₁: a média geométrica do speedup sqlite/duckdb_t4 em OLAP é 1. H1₁: é diferente de 1.
  - H0₂: speedup sqlite/duckdb_t1 = 1 (colunar sem paralelismo).
  - H0₃: speedup duckdb_t1/duckdb_t4 = 1.
  - H0₄: em OLTP, `ops_sec` do SQLite = DuckDB. H1₄: é diferente.
  - H0₅: o speedup não muda entre sf 0,1 e 1 (comparação descritiva dos ICs).
- [x] **Passo 4:** variáveis:
  - independentes: `engine`, `sf`, `workload`;
  - dependentes: as métricas acima;
  - fixas: `sqlite_settings`, `duckdb_settings`, `limits`, hardware;
  - de confusão: cache do SO, temperatura, processos de fundo → mitigação.

  Justificar o tratamento **duckdb_t1**: é ele que permite separar o motor colunar do paralelismo.
- [x] **Passo 5:** seção *Armadilhas de medição*.
  - **Goodhart:** dá para "jogar" o benchmark deixando o SQLite sem índices, por isso o SQLite recebe índices nas FKs, como em produção.
  - **Campbell/McNamara:** o que não medimos (concorrência entre vários processos, durabilidade, tamanho do binário, facilidade de uso).
  - O TPC-H é carga **sintética**.
- [ ] **Passo 6:** **(integrante)** commit `docs: GQM, hipóteses e design`.

### Tarefa A-1.4: 7 categorias v1 + plano de coleta e análise

**Files:** Create: `docs/03-categorias.md`, `docs/04-plano-coleta-analise.md`

- [x] **Passo 1:** em `03`, uma tabela com as 7 categorias, cada uma com 2–3 linhas de justificativa. Marcar como "v1". Proposta:

  | Categoria | Classificação |
  |---|---|
  | Natureza | aplicada |
  | Objetivo | explicativo |
  | Abordagem | quantitativa |
  | Procedimento | experimental (experimento controlado em laboratório, medidas repetidas) |
  | Tempo | transversal |
  | Controle | alto |
  | Nível de evidência | experimento controlado com validade externa limitada |
- [x] **Passo 2:** `04` contém:
  - o **protocolo**: preflight → `make data` → snapshot do ambiente → para cada bloco sorteado: container novo, aquecimento, itens em ordem sorteada, timeout por consulta, coleta do pico de RSS → JSON;
  - a **checagem de correção**: mesmo `result_hash` entre os bancos;
  - as **regras de ética**: tudo local, dados sintéticos;
  - o **critério de run válido**: sem `error`, e hash igual ao de referência ou `timeout=True`;
  - o **tratamento de timeout** (dado censurado);
  - o **plano estatístico**, copiado da seção acima;
  - os **critérios do piloto**:
    1. se o poder simulado com n = 10 para δ = 0,33 em C1 for < 0,8 em mais de 20% das células, aumentar `repetitions.full`;
    2. consulta que der timeout nas 3 rodadas do piloto vai para `censored_queries`.
- [ ] **Passo 3:** **(integrante)** commit `docs: categorias v1 e plano de coleta/análise`.

> ✅ Fim de A na Sprint 1. B pode começar.

## Integrante B — Sprint 1

### Tarefa B-1.1: Imagem Docker + geração e carga dos dados

**Files:**
- Create: `infra/Dockerfile`, `bench/datagen.py`, `tests/test_datagen.py`
- Modify: `Makefile` (alvo `data`)

**Interfaces:**
- Consumes: `bench/config.yaml`
- Produces:
  - `generate(sf: float, out_dir: Path = Path("data/db")) -> tuple[Path, Path]`. Cria `tpch_sf{sf}.duckdb` (com `INSTALL tpch; LOAD tpch; CALL dbgen(sf=…)`) e `tpch_sf{sf}.sqlite` (cópia das 8 tabelas com a extensão `sqlite` do DuckDB: `ATTACH … (TYPE sqlite)`, convertendo datas para texto ISO `YYYY-MM-DD` e DECIMAL para DOUBLE). Depois aplica as PKs e índices de `SQLITE_INDEXES` via `apsw` e roda `ANALYZE`. Não faz nada se os dois arquivos já existirem e o hash bater com o manifest.
  - `SQLITE_INDEXES: list[str]`: `CREATE INDEX` para as PKs e para estas FKs: `l_orderkey`, `l_partkey`, `l_suppkey`, `o_custkey`, `ps_partkey`, `ps_suppkey`, `c_nationkey`, `s_nationkey`, `n_regionkey`.
  - `table_counts(db: Path) -> dict[str, int]`.
- [ ] **Passo 1:** `Dockerfile`: `python:3.12-slim`, `pip install -r requirements.lock`, copiar `bench/` e `ENTRYPOINT ["python", "-m", "bench.runner"]`.
- [ ] **Passo 2 (teste falhando)**, com `sf=0.01` em `tmp_path`:
  - `test_generate_creates_both`;
  - `test_counts_match_across_engines` (as 8 tabelas com contagens iguais nos dois bancos);
  - `test_fixed_counts` (`nation=25`, `region=5`, `orders=15000` com sf 0,01);
  - `test_sqlite_has_indexes` (`PRAGMA index_list('lineitem')` não vazio);
  - `test_generate_idempotent` (a segunda chamada não regrava, comparando o mtime).
- [ ] **Passo 3:** FAIL → implementar → PASS. Rodar `make data`, que gera sf 0,1 e 1 (o sf 1 ocupa cerca de 2–3 GB no total), e registrar os hashes no manifest.
- [ ] **Passo 4:** **(integrante)** commit `feat(bench): imagem docker e geração/carga TPC-H`.

### Tarefa B-1.2: Consultas nos dois dialetos + hash de resultado + OLTP

**Files:**
- Create: `bench/queries/duckdb/q01..q22.sql`, `bench/queries/sqlite/q01..q22.sql`, `bench/result_hash.py`, `bench/oltp.py`
- Test: `tests/test_queries.py`, `tests/test_result_hash.py`, `tests/test_oltp.py`

**Interfaces:**
- Produces:
  - `load_query(engine_kind: Literal["duckdb","sqlite"], qid: str) -> str`
  - `result_hash(rows: list[tuple]) -> str`: arredonda floats para 2 casas, converte datas para ISO, ordena as linhas e devolve o SHA-256 do `repr`. Primeiros 16 caracteres.
  - `run_oltp(conn, kind: str, op: Literal["point_select","insert","update"], n_ops: int, seed: int) -> dict` → `{elapsed_ms, ops_sec, p99_ms}`. Detalhes:
    - `point_select` busca `orders` por `o_orderkey` aleatório;
    - `insert` insere em `orders_bench`, uma cópia vazia de `orders` criada no início;
    - `update` altera `o_comment` por chave aleatória;
    - cada operação é uma transação (autocommit);
    - a latência é medida por operação com `time.perf_counter_ns`.
- [ ] **Passo 1:** as consultas DuckDB vêm de `SELECT query FROM tpch_queries()`, salvas em arquivo. A versão SQLite é traduzida à mão com estas trocas:
  - `date 'X' + interval 'N' day` → `date('X','+N day')`;
  - `extract(year from c)` → `CAST(strftime('%Y', c) AS INTEGER)`;
  - `substring(c from a for b)` → `substr(c, a, b)`;
  - remover `::` casts.

  Comentar no topo de cada arquivo as alterações feitas.
- [ ] **Passo 2 (testes falhando):**
  - `test_all_queries_present` (22 × 2 arquivos);
  - `test_result_hash_order_independent`;
  - `test_result_hash_rounds_floats`;
  - `test_results_match_across_engines[q01..q22]` (parametrizado, em sf 0,01, mesmo hash nos dois bancos);
  - `test_oltp_returns_metrics` (os 3 ops nos 2 bancos, `ops_sec > 0`, `p99_ms >= 0`);
  - `test_oltp_insert_does_not_touch_orders` (contagem de `orders` inalterada).
- [ ] **Passo 3:** FAIL → corrigir as traduções até os 22 hashes baterem → PASS. **Não seguir adiante com nenhum hash diferente.**
- [ ] **Passo 4:** **(integrante)** commit `feat(bench): consultas TPC-H nos 2 dialetos, hash e OLTP`.

### Tarefa B-1.3: Agenda sorteada, runner e orquestrador (resume, timeout, preflight)

**Files:**
- Create: `bench/schedule.py`, `bench/runner.py`, `bench/run_matrix.py`, `bench/env_snapshot.py`
- Test: `tests/test_schedule.py`, `tests/test_run_matrix.py`

**Interfaces:**
- Produces:
  - `@dataclass(frozen=True) Block(block_id: str, phase: str, order: int, engine: str, sf: float, workload: str, round: int)`
  - `build_schedule(cfg: dict, phase: Literal["pilot","full"]) -> list[Block]`: produto engines × sf × workloads × rodadas, embaralhado com `random.Random(cfg["seed"] + {"pilot":0,"full":1}[phase])`. Na fase full, os itens de `censored_queries` ficam só nas rodadas ≤ `reps_censored_full`, controlado em `items_for(block, cfg) -> list[str]`.
  - `items_for(block: Block, cfg: dict) -> list[str]`: lista de itens sorteada com `seed + block.order`.
  - `runner.run_block(block: Block, cfg: dict) -> dict` (dentro do container): abre a conexão com as configs (`threads`, `memory_limit` ou os PRAGMAs do SQLite), aquece e roda cada item. O timeout de consulta é por *watchdog thread*: `conn.interrupt()` no DuckDB e `apsw` `Connection.interrupt()` no SQLite. Mede `peak_rss_mb` com `psutil`. Devolve `{"block":…, "env":{engine_version,…}, "items":[{item, elapsed_ms, ops_sec, p99_ms, rows_returned, result_hash, timeout, error}], "complete": true}`.
  - `run_matrix.execute_block(block, cfg, out_dir) -> Path`: `docker run --rm --cpus=<cpus> --memory=<mem_gb>g -v data/db:/data/db:ro …` (o OLTP precisa de escrita: montar uma cópia temporária do banco por bloco). Grava `out_dir/<block_id>.json`.
  - `pending(schedule, out_dir) -> list[Block]`: pula blocos cujo JSON existe com `"complete": true`.
  - `preflight(cfg, cpu_count=None, mem_gb=None, free_disk_gb=None) -> None` → `SystemExit` com mensagem.
  - `append_results(raw_json: Path, csv_path: Path, reference_hashes: dict) -> None`: uma linha por item. `valid` vem de `analysis.lab05.validate.run_is_valid`.
  - CLI `python -m bench.run_matrix --phase pilot|full [--resume] [--dry-run]`.
- [ ] **Passo 1 (testes falhando):**
  - `test_schedule_size`: pilot = 3·2·2·3 = 36 blocos;
  - `test_schedule_deterministic`;
  - `test_pilot_full_differ`;
  - `test_block_id_format`: `"pilot-duckdb_t4-sf0.1-olap-r01"`;
  - `test_items_shuffled_but_complete`: os 22 itens, ordem diferente entre blocos;
  - `test_censored_only_first_rounds`;
  - `test_resume_skips_done_blocks`;
  - `test_preflight_rejects_small_host`;
  - `test_timeout_marks_item`: consulta artificial lenta com `timeout_ms=100` → `timeout=True`, `elapsed_ms ≈ 100`.
- [ ] **Passo 2:** FAIL → implementar → PASS. Conferir os comandos com `--dry-run`.
- [ ] **Passo 3:** **(integrante)** commit `feat(bench): agenda sorteada, runner, orquestrador, resume e preflight`.

### Tarefa B-1.4: Validação + manifest + poder + coleta piloto

**Files:**
- Create: `analysis/lab05/__init__.py`, `load.py`, `validate.py`, `power.py`, `tests/fixtures/results_small.csv`, `tests/test_validate.py`, `tests/test_power.py`, `docs/05-piloto.md`
- Modify: `Makefile` (`preflight`, `pilot`, `run`, `validate`, `test`)

**Interfaces:**
- Produces:
  - `load_results(path: str | Path = "data/processed/results.csv") -> pd.DataFrame`
  - `run_is_valid(row: Mapping) -> bool`: `error` vazio E (`timeout` OU `result_hash == hash de referência do item/sf`). A referência é o hash do DuckDB.
  - `validate(df: pd.DataFrame, cfg: dict, phase: str) -> list[str]`: problemas (n por célula ≠ esperado, `run_id` duplicado, run inválido, hash divergente) e avisos (`"AVISO tendência …"`, `"INFO timeouts: sqlite sf1 q17 = 3/3"`, outliers por IQR 1,5, que são só **sinalizados**, nunca removidos)
  - `write_manifest(paths: list[Path], out: Path) -> None`
  - `simulate_power(x, y, n: int, n_sim: int = 2000, alpha: float = 0.05, seed: int = 20262) -> float` (reuso do Lab04: reamostra o piloto e devolve a fração de Mann-Whitney com p < α)
- [ ] **Passo 1 (testes falhando):**
  - `test_validate_flags_error`;
  - `test_validate_flags_hash_mismatch`;
  - `test_validate_counts_timeouts` (timeout é válido, mas é contado);
  - `test_validate_flags_missing_reps`;
  - `test_validate_flags_duplicate_run_id`;
  - `test_validate_warns_on_trend`;
  - `test_validate_clean_returns_empty`;
  - `test_power_identical_near_alpha` (0,02–0,09);
  - `test_power_shifted_high` (> 0,95).

  FAIL → implementar → PASS.
- [ ] **Passo 2:** Makefile: `pilot` = `preflight` + `snapshot` + `run_matrix --phase pilot --resume` + `validate` + `manifest`.
- [ ] **Passo 3:** fechar programas, deixar o notebook na tomada e no modo alto desempenho. Rodar `make pilot`. O SQLite em sf 1 domina o tempo, com estimativa de 1–3 h. Esperado: `validate` sem *problemas*.
- [ ] **Passo 4:** `docs/05-piloto.md` com:
  - o ambiente (`env.json`);
  - uma tabela de mediana por engine × sf × item;
  - os timeouts;
  - os avisos;
  - o poder simulado para n = 10 (C1) por célula;
  - as **decisões**: atualizar `repetitions.full` e `censored_queries` no config;
  - a estimativa de duração da coleta completa.
- [ ] **Passo 5:** **(integrante)** commit `data: coleta piloto validada` + tag `pilot-v1`. Entregar S01: link do repo/Project + docs 01–05.

---

# SPRINT 2 — Coleta completa + análise + ameaças (5 pts)

## Integrante A — Sprint 2

> Trabalha **só com os dados do piloto** (`pilot-v1`). O código fica pronto para B rodar nos dados completos.

### Tarefa A-2.1: Estatística descritiva

**Files:** Create: `analysis/lab05/descriptive.py`, `tests/test_descriptive.py`

**Interfaces:**
- Consumes: `load_results` (B-1.4)
- Produces: `describe_by_cell(df, metric: str, by: tuple[str, ...] = ("engine","sf","workload","item")) -> pd.DataFrame` com `n, n_timeout, mean, sd, median, q1, q3, iqr, min, max, cv, geomean`. Usa só `valid == True`.

- [ ] **Passo 1:** escrever `test_describe_columns`, `test_describe_ignores_invalid`, `test_describe_values` (mediana, IQR e média geométrica exatos) e `test_describe_counts_timeouts`. FAIL → implementar → PASS.
- [ ] **Passo 2:** **(integrante)** commit `feat(analysis): estatística descritiva por célula`.

### Tarefa A-2.2: Testes de hipótese, speedup e tamanho de efeito

**Files:** Create: `analysis/lab05/stats_tests.py`, `tests/test_stats_tests.py`

**Interfaces:**
- Produces:
  - `cliffs_delta(x, y) -> float` em [-1, 1]. Positivo significa x > y.
  - `magnitude(d: float) -> Literal["desprezível","pequeno","médio","grande"]` (|d| < 0,147 / < 0,33 / < 0,474 / resto)
  - `bootstrap_ci(x, y, stat=lambda a, b: np.median(a)/np.median(b), n_boot=5000, seed=20262) -> tuple[float, float]`
  - `holm(pvals: Sequence[float]) -> np.ndarray`
  - `compare_pair(df, metric: str, a: str, b: str, cell_cols=("sf","item")) -> pd.DataFrame`: uma linha por célula com `comparison ("a_vs_b"), n_a, n_b, n_timeout_a, n_timeout_b, shapiro_p_a, shapiro_p_b, test ("welch-log"|"mann-whitney"|"insuficiente"), stat, p, p_holm, reject_h0, cliffs_delta, magnitude, median_a, median_b, speedup (median_a/median_b), ci_low, ci_high`. O Holm é aplicado por `sf`.
  - `across_items(df, a: str, b: str, sf: float, workload: str = "olap") -> dict`: `{n_items, geomean_speedup, ci_low, ci_high, wilcoxon_stat, wilcoxon_p, wins_b}`. Usa a mediana por item de cada engine, `speedup_i = med_a/med_b`, `geomean = exp(mean(log speedup_i))`, faz bootstrap sobre os itens e aplica `scipy.stats.wilcoxon` em `log speedup_i`.
- [ ] **Passo 1:** escrever os testes:
  - `test_cliffs_delta_extremes`;
  - `test_magnitude_thresholds` (0,1 / 0,2 / 0,4 / 0,5);
  - `test_holm_known_values` (`[0.01, 0.04, 0.03]` → `[0.03, 0.06, 0.06]`);
  - `test_compare_picks_welch_log_for_lognormal`;
  - `test_compare_picks_mw_for_bimodal`;
  - `test_speedup_direction` (a 10× mais lento que b → speedup ≈ 10);
  - `test_compare_with_censored` (timeouts entram com `elapsed_ms = timeout_ms` e não quebram);
  - `test_compare_handles_zero_variance` (constantes, n < 3 → `"insuficiente"`);
  - `test_across_items_geomean` (speedups 2, 8 → geomean 4).

  FAIL → implementar → PASS.
- [ ] **Passo 2:** **(integrante)** commit `feat(analysis): testes, Holm, Cliff's delta, speedup e análise entre consultas`.

### Tarefa A-2.3: Gráficos + gerador de relatório

**Files:** Create: `analysis/lab05/plots.py`, `analysis/lab05/report.py`. Modify: `Makefile` (alvo `analyze`)

**Interfaces:**
- Produces:
  - `speedup_bars(cmp_df, out: Path) -> Path`: barras do speedup por consulta, em **escala log**, com IC. Um painel por sf e uma linha em 1×.
  - `boxplot_items(df, items: list[str], out: Path) -> Path`: `elapsed_ms` (log) por engine para as consultas escolhidas.
  - `decomposition_plot(across: dict, out: Path) -> Path`: geomean C2 (colunar) × C3 (paralelismo) × C1 (total), por sf.
  - `oltp_plot(df, out: Path) -> Path`: `ops_sec` e `p99_ms` por engine e operação.
  - CLI `python -m analysis.lab05.report --phase pilot|full`: roda `validate` → `describe_by_cell` → `compare_pair` (C1, C2, C3) → `across_items` → figuras em `analysis/figures/<phase>/` → `docs/07-resultados.md`. O doc tem tabelas Markdown, links das figuras e um parágrafo-modelo por hipótese ("rejeita/não rejeita H0, speedup geomean = …×, IC …, δ …").
- [ ] **Passo 1:** `make analyze PHASE=pilot` gera o `docs/07` provisório sem erro. Abrir e conferir cada PNG.
- [ ] **Passo 2:** **(integrante)** commit `feat(analysis): gráficos e relatório automático`.

### Tarefa A-2.4: Ameaças à validade

**Files:** Create: `docs/06-ameacas.md`

- [ ] **Passo 1:** tabela *Tipo | Ameaça | Impacto | Mitigação | Status*, com ≥ 2 ameaças por tipo:

  | Tipo | Ameaças | Mitigação |
  |---|---|---|
  | **Conclusão** | n pequeno por célula; muitas comparações; timeouts censurados | simulação de poder, Holm, censura conservadora e relatada |
  | **Interna** | cache do SO e ordem; temperatura; tradução de consulta diferente | blocos em container novo com aquecimento igual, ordem sorteada, teste de tendência, `result_hash` |
  | **Construto** | TPC-H ≠ carga real; tempo de parede ≠ experiência do usuário; índices escolhidos por nós | dois workloads, dois sf, índices documentados como "configuração típica de produção" |
  | **Externa** | uma máquina x86; versões específicas; sem concorrência entre processos; dados até 1 GB | `env.json`; `08` deixa claro o que não se pode generalizar |
- [ ] **Passo 2:** **(integrante)** commit `docs: ameaças à validade`.

> ✅ Fim de A na Sprint 2. B pode começar.

## Integrante B — Sprint 2

### Tarefa B-2.1: Coleta completa

- [ ] **Passo 1:** ler os docs 06 e 07 (piloto). `make test` → tudo PASS.
- [ ] **Passo 2:** `make run` (fase full; usar a estimativa do `05-piloto.md`). Rodar de madrugada, na tomada e sem uso. Se cair, rodar `make run` de novo (o `--resume` continua de onde parou).
- [ ] **Passo 3:** `make validate`. Esperado: nenhum *problema*. Se algum bloco for inválido, apagar só aquele JSON, rodar de novo e registrar tudo em `docs/05-piloto.md` § "Coleta completa".
- [ ] **Passo 4:** gerar o manifest; **(integrante)** commit `data: coleta completa validada`, tag `data-v1`.

### Tarefa B-2.2: Rodar a análise e interpretar

**Files:** Modify: `docs/07-resultados.md`

- [ ] **Passo 1:** `make analyze PHASE=full`.
- [ ] **Passo 2:** seção "Interpretação": responder Q1–Q5 do GQM. Destacar:
  - as consultas com o maior e o menor speedup, e por quê (agregações em scan de `lineitem` × buscas seletivas por índice);
  - quanto do ganho é colunar (C2) e quanto é paralelismo (C3);
  - se o speedup cresce de sf 0,1 para 1;
  - se o SQLite vence em OLTP.
- [ ] **Passo 3:** conferir a coerência entre texto, tabelas e figuras: o sinal de δ, IC que não cruza 1× quando `reject_h0`, timeouts citados.
- [ ] **Passo 4:** **(integrante)** commit `docs: resultados da coleta completa`. Entregar S02.

---

# SPRINT 3 — Impacto + categorias revisadas + conclusões + rascunhos (5 pts)

## Integrante A — Sprint 3

### Tarefa A-3.1: Fontes de impacto + cálculo

**Files:** Modify: `docs/impacto/fontes.yaml`. Create: `analysis/lab05/impact.py`, `tests/test_impact.py`, `docs/08-impacto.md`

**Interfaces:**
- Consumes: `across_items` (A-2.2), `fontes.yaml`
- Produces: `estimate_impact(speedup: float, scenario: dict) -> dict`. Entrada `scenario = {nome, pessoas, consultas_por_dia, tempo_medio_s_sqlite, dias_uteis_ano}`. Saída `{nome, tempo_medio_s_duckdb, horas_economizadas_dia, horas_economizadas_ano}`. A hipótese explícita (o tempo de cada consulta escala pelo speedup medido) entra em `08` como limitação.
- [ ] **Passo 1:** coletar números públicos com link e data:
  - quantos desenvolvedores e analistas usam SQLite/DuckDB (Stack Overflow Developer Survey);
  - downloads mensais do DuckDB (pypistats);
  - adoção do SQLite segundo a página oficial.

  Montar 3 cenários: analista individual, time de dados de 10 pessoas e o ecossistema (downloads/mês × uso típico, marcado como **estimativa de ordem de grandeza**). Salvar um print por fonte em `docs/evidencias/`.
- [ ] **Passo 2 (testes):**
  - `test_impact_no_speedup_no_savings` (speedup 1 → 0);
  - `test_impact_known_values` (speedup 4, 1 pessoa, 100 consultas de 60 s → 1,25 h/dia);
  - `test_impact_slower_is_negative` (speedup 0,5 → horas negativas).

  FAIL → implementar → PASS.
- [ ] **Passo 3:** escrever `08-impacto.md` com:
  - a frase-modelo do enunciado ("Com X consultas por dia, o DuckDB economiza Y horas…");
  - a tabela de cenários;
  - a recomendação para OLTP (onde o SQLite pode ser melhor);
  - a seção **"O que NÃO podemos afirmar"**: concorrência, dados > 1 GB ou > RAM, ARM/celular (onde o SQLite domina), cargas reais, versões futuras, tudo ligado à validade externa.
- [ ] **Passo 4:** **(integrante)** commit `feat(impact): estimativa de impacto com fontes`.

### Tarefa A-3.2: 7 categorias revisadas

**Files:** Modify: `docs/03-categorias.md`

- [ ] **Passo 1:** revisar cada categoria com base no que foi de fato feito. Por exemplo: experimento controlado + dados públicos de adoção → procedimento misto. Medidas repetidas e pareamento por consulta → mais controle. Justificar cada categoria e discutir **o que isso significa para a força da evidência**. Marcar "v2" e manter a v1 num `<details>`.
- [ ] **Passo 2:** **(integrante)** commit `docs: categorias revisadas`.

### Tarefa A-3.3: Reaproveitamento dos labs

**Files:** Create: `docs/10-reaproveitamento.md`

- [ ] **Passo 1:** tabela *Lab | O que reaproveitamos | Onde está | O que é novo*:
  - **Lab01:** coleta automatizada + Kanban no GitHub Projects;
  - **Lab02:** desenho com tratamentos (3 tratamentos, incluindo o de controle duckdb_t1);
  - **Lab03:** DORA → tempo de resposta e p99 como SLI de um serviço que usa o banco;
  - **Lab04:** escolha do teste, simulação de poder, dashboard.
- [ ] **Passo 2:** **(integrante)** commit `docs: reaproveitamento dos labs`.

> ✅ Fim de A na Sprint 3. B pode começar.

## Integrante B — Sprint 3

### Tarefa B-3.1: Conclusões e limitações

**Files:** Create: `docs/09-conclusoes.md`

- [ ] **Passo 1:** responder às duas perguntas do enunciado. "O que o estudo mostrou?" vem do `07`. "O que significa para quem usa?" vem do `08`. Incluir uma recomendação prática no formato *"se você faz agregações sobre milhões de linhas, use X; se faz leitura/escrita de linhas individuais num app, use Y"*. As limitações referenciam o `06`.
- [ ] **Passo 2:** **(integrante)** commit `docs: conclusões e limitações`.

### Tarefa B-3.2: Dashboard interativo

**Files:** Create: `analysis/dashboard/app.py`. Modify: `Makefile` (`dashboard`)

- [ ] **Passo 1:** Streamlit com:
  - filtros (sf, workload, comparação C1/C2/C3, consulta);
  - gráfico de speedup;
  - boxplot da consulta escolhida;
  - tabela do `compare_pair`;
  - calculadora de impacto (sliders de pessoas, consultas por dia e tempo médio chamando `estimate_impact`).
- [ ] **Passo 2:** `make dashboard` → `localhost:8501` sem erro, com todos os filtros testados.
- [ ] **Passo 3:** **(integrante)** commit `feat(dashboard): dashboard interativo`.

### Tarefa B-3.3: Rascunho do documento e da apresentação

**Files:** Create: `docs/relatorio/relatorio.md`, `docs/apresentacao/roteiro.md`

- [ ] **Passo 1:** montar `relatorio.md` a partir dos docs, nesta ordem:
  1. Introdução e software (01)
  2. Pergunta e caminho (02)
  3. Categorias (03)
  4. Método (04, 05)
  5. Resultados (07)
  6. Ameaças (06)
  7. Impacto (08)
  8. Conclusões (09)
  9. Reaproveitamento (10)
  10. Referências (`fontes.yaml`)
- [ ] **Passo 2:** `roteiro.md` com 10 minutos cronometrados:

  | Tempo | Bloco |
  |---|---|
  | 1:00 | Os dois softwares e os números |
  | 1:00 | Pergunta e GQM |
  | 1:00 | Categorias |
  | 1:30 | Método (3 tratamentos, TPC-H, hash de correção) |
  | 2:30 | Resultados (demo do dashboard: "rode a Q1 nos dois") |
  | 1:00 | Ameaças |
  | 1:30 | Impacto e o que não se pode afirmar |
  | 0:30 | Conclusão |

  Formato sugerido: **"reunião com o tech lead decidindo qual banco embarcar no produto de dados"**.
- [ ] **Passo 3:** **(integrante)** commit `docs: rascunho do relatório e da apresentação`. Entregar S03.

---

# SPRINT FINAL — Documento final + apresentação (5 pts)

## Integrante A — Final

### Tarefa A-F.1: Documento final

**Files:** Modify: `docs/relatorio/relatorio.md`, `README.md`

- [ ] **Passo 1:** revisar o relatório contra o checklist da seção 8 do enunciado, item a item:
  - software + 3 critérios com números;
  - pergunta + caminho;
  - 7 categorias justificadas;
  - conceitos da teórica (GQM, escalas, Goodhart/Campbell/McNamara, ameaças);
  - reaproveitamento;
  - resultados com análise adequada à escala;
  - 4 tipos de ameaças;
  - impacto + o que não se pode afirmar.
- [ ] **Passo 2:** regerar com `make analyze PHASE=full` e conferir que todo número do texto bate com o `07`/`08`. Conferir que cada fonte tem link e data.
- [ ] **Passo 3:** `README.md` com a seção "Como reproduzir": `make preflight && make data && make pilot && make run && make analyze PHASE=full && make dashboard`. Opcional: PDF via `pandoc`.
- [ ] **Passo 4:** **(integrante)** commit `docs: documento final`.

### Tarefa A-F.2: Guia de defesa

**Files:** Create: `docs/guia-defesa.md`

- [ ] **Passo 1:** 20+ perguntas prováveis com respostas curtas, cobrindo **também as partes de B**. Exemplos:
  - Por que média geométrica do speedup e não média aritmética?
  - Por que Mann-Whitney / Welch em log?
  - Qual a escala de `elapsed_ms`?
  - O que significa Cliff's δ = 0,8?
  - Por que existe o duckdb_t1?
  - Como garantem que as consultas fazem a mesma coisa nos dois bancos?
  - O que fizeram com os timeouts?
  - Dar índices ao SQLite não favorece um lado?
  - Por que isso não é mineração de repositório?
- [ ] **Passo 2:** **(integrante)** commit `docs: guia de defesa`.

> ✅ Fim de A na Final. B pode começar.

## Integrante B — Final

### Tarefa B-F.1: Apresentação final

**Files:** Create: `docs/apresentacao/slides.*`

- [ ] **Passo 1:** slides seguindo o `roteiro.md`, com os mesmos números do relatório final. Incluir um slide "Reaproveitado × novo".
- [ ] **Passo 2:** preparar a demo ao vivo: `make dashboard` aberto antes, e um script `demo.py` que roda a Q1 em sf 0,1 nos dois bancos e mostra o tempo. Gravar um vídeo de backup de 1 min.
- [ ] **Passo 3:** **(integrante)** commit `docs: apresentação final`.

### Tarefa B-F.2: Ensaio e entrega

- [ ] **Passo 1:** ensaio cronometrado com A (≤ 10 min). Cada um responde 5 perguntas do `guia-defesa.md` sobre a parte do **outro**.
- [ ] **Passo 2:** `make test` → PASS. Tag `v1.0-entrega`. Conferir que o link do repo/Project está na entrega.
- [ ] **Passo 3:** fechar os cards do Kanban e entregar no Canvas.

---

## Kanban (GitHub Projects)

**Colunas:** Backlog → Sprint atual → Em andamento → Revisão → Concluído
**Labels:** `integrante-A` · `integrante-B` · `sprint-1` · `sprint-2` · `sprint-3` · `sprint-final` · `doc` · `codigo` · `dados`
**Regra:** um card de B só sai do Backlog quando todos os cards de A da mesma sprint estão em *Concluído*. Cada card fecha com um commit/PR que o referencia (`closes #N`).

### Integrante A
| Sprint | Card | Labels | Critério de pronto |
|---|---|---|---|
| 1 | A-1.1 Estrutura do repo, convenções, config.yaml, lockfile e Kanban | codigo | `pytest` roda; Project com todos os cards |
| 1 | A-1.2 DuckDB e SQLite: evidências dos 3 critérios | doc | Tabela por software com fonte e data; OK do professor |
| 1 | A-1.3 GQM, hipóteses H1–H5, variáveis e design | doc | Template Basili; escala de cada métrica; justificativa do duckdb_t1 |
| 1 | A-1.4 7 categorias v1 + plano de coleta/análise | doc | Protocolo, critério de validade, timeout, plano estatístico, critérios do piloto |
| 2 | A-2.1 Estatística descritiva | codigo | 4 testes passando |
| 2 | A-2.2 Testes, Holm, Cliff's δ, speedup, análise entre consultas | codigo | 9 testes passando, incluindo censura e variância zero |
| 2 | A-2.3 Gráficos + gerador de relatório | codigo | `make analyze PHASE=pilot` gera o `07` e as figuras |
| 2 | A-2.4 Ameaças à validade (4 tipos) | doc | ≥ 2 por tipo, com mitigação |
| 3 | A-3.1 Fontes e cálculo de impacto | codigo, doc | `fontes.yaml` com link e data; 3 cenários; "o que não podemos afirmar" |
| 3 | A-3.2 7 categorias revisadas | doc | v2 justificada + força da evidência |
| 3 | A-3.3 Reaproveitamento dos labs | doc | Tabela Lab01–04 |
| F | A-F.1 Documento final | doc | Checklist da seção 8 completo; números conferidos |
| F | A-F.2 Guia de defesa | doc | ≥ 20 perguntas, cobrindo as partes de B |

### Integrante B
| Sprint | Card | Labels | Critério de pronto |
|---|---|---|---|
| 1 | B-1.1 Dockerfile + geração/carga TPC-H nos 2 bancos | codigo, dados | 5 testes passando; `make data` gera sf 0,1 e 1 |
| 1 | B-1.2 22 consultas nos 2 dialetos + hash + OLTP | codigo | **22/22 hashes iguais**; testes OLTP passando |
| 1 | B-1.3 Agenda sorteada, runner, orquestrador, resume, timeout, preflight | codigo | 9 testes passando; `--dry-run` ok |
| 1 | B-1.4 Validação, manifest, poder + coleta piloto | codigo, dados, doc | Piloto válido; tag `pilot-v1`; decisões de n e censura no `05` |
| 2 | B-2.1 Coleta completa | dados | `validate` sem problemas; tag `data-v1`; manifest |
| 2 | B-2.2 Rodar análise + interpretação | doc | `07` final respondendo Q1–Q5 |
| 3 | B-3.1 Conclusões e limitações | doc | Responde às 2 perguntas + recomendação prática |
| 3 | B-3.2 Dashboard Streamlit | codigo | Filtros + calculadora de impacto funcionando |
| 3 | B-3.3 Rascunho do relatório e roteiro | doc | Relatório montado; roteiro de 10 min |
| F | B-F.1 Apresentação final | doc | Slides + demo + vídeo de backup |
| F | B-F.2 Ensaio e entrega | — | ≤ 10 min; tag `v1.0-entrega`; entregue no Canvas |
