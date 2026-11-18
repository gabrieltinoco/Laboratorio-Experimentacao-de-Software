# 04 — Plano de coleta e de análise

Parâmetros: [`bench/config.yaml`](../bench/config.yaml). Hipóteses e métricas: [02](02-gqm-hipoteses.md).

## 1. Protocolo de coleta

```
make preflight ─► make data ─► snapshot do ambiente ─► para cada bloco (ordem sorteada):
                                                         container novo
                                                         ├─ conexão com as configurações do tratamento
                                                         ├─ aquecimento (count(*) em cada tabela, sem medir)
                                                         ├─ itens em ordem sorteada, cada um 1 vez
                                                         │    └─ timeout por consulta (120 s)
                                                         ├─ pico de RSS do processo
                                                         └─ data/raw/<phase>/<block_id>.json
                                                     ─► results.csv ─► validate ─► manifest.json
```

1. **Preflight:** o processo aborta se o host tiver menos núcleos que `limits.cpus` (4), menos RAM que `limits.mem_gb` + 2 (10 GB) ou menos de 10 GB de disco livre.
2. **Dados:** `make data` gera o TPC-H em sf 0,1 e 1 com a extensão `tpch` do DuckDB e copia as 8 tabelas para o SQLite (datas como texto ISO, DECIMAL como DOUBLE). Depois cria as PKs e os índices nas FKs e roda `ANALYZE`. O processo é determinístico, e o SHA-256 dos arquivos vai para `data/manifest.json`.
3. **Snapshot do ambiente:** `data/raw/env.json` guarda CPU, núcleos, RAM, SO, versão do Docker, `duckdb.__version__` e `apsw.sqlitelibversion()`.
4. **Agenda:** o produto engines × sf × workloads × rodadas é embaralhado com `random.Random(seed + {pilot: 0, full: 1})`. Isso dá 36 blocos no piloto e 120 na coleta completa (com 10 rodadas).
5. **Bloco:** `docker run --rm --cpus=4 --memory=8g`, com os bancos montados como somente leitura (o OLTP usa uma cópia temporária por bloco). Dentro do bloco:
   - aquecimento;
   - itens na ordem sorteada (`seed + order`);
   - tempo medido com `time.perf_counter_ns`;
   - pico de RSS com `psutil`.
6. **Retomada:** `--resume` pula os blocos cujo JSON já existe com `"complete": true`. Isso evita linhas duplicadas.
7. **Condições da máquina:** na tomada, em modo de alto desempenho, sem outros programas abertos e, de preferência, de madrugada.

## 2. Checagem de correção

Toda consulta precisa produzir o **mesmo `result_hash`** nos dois bancos. O hash é calculado assim:

1. arredondar os floats para 2 casas;
2. converter as datas para ISO;
3. ordenar as linhas;
4. tirar o SHA-256 do `repr` e ficar com os 16 primeiros caracteres.

O hash de referência de cada `(sf, item)` é o do DuckDB. Sem essa checagem, uma tradução errada para o dialeto do SQLite (datas, `interval`, `extract`, `substring`) faria o estudo comparar consultas diferentes. O teste `test_results_match_across_engines[q01..q22]` bloqueia a coleta enquanto houver qualquer hash diferente.

## 3. Ética

- Tudo roda localmente, na máquina do grupo. Nenhum sistema de terceiros recebe carga.
- Os dados são sintéticos (TPC-H). Não há dados pessoais nem participantes humanos.
- O software é usado como produto em execução. Não há mineração de repositórios nem análise de código-fonte de terceiros.
- Os números públicos de adoção (Sprint 3) vêm de páginas abertas, com link e data de acesso.

## 4. Critério de run válido

Uma linha de `results.csv` é **válida** (`valid = True`) se:

- `error` está vazio; **e**
- `result_hash` é igual ao hash de referência do `(sf, item)`, **ou** `timeout = True`.

Uma linha inválida não entra na análise. O bloco é apagado (o JSON inteiro), roda de novo e o fato é registrado em `05-piloto.md`. **Nunca se edita `data/raw/`.**

A validação (`validate`) também emite:

- **problemas**, que bloqueiam a análise: n por célula diferente do esperado, `run_id` duplicado, run inválido, hash divergente;
- **avisos**, que não bloqueiam:
  - tendência: Spearman entre `order` e `elapsed_ms` por célula, com alerta se |ρ| > 0,3 e p < 0,05;
  - contagem de timeouts;
  - outliers pela regra de 1,5 × IQR, que são **sinalizados, nunca removidos**.

## 5. Tratamento de timeout (dado censurado)

Uma consulta que estoura `timeout_ms` (120 s) é interrompida (`conn.interrupt()`) e registrada com `elapsed_ms = timeout_ms` e `timeout = True`. Ela **não** é descartada:

- descartar faria o SQLite parecer melhor do que é, porque justamente as consultas mais lentas sumiriam;
- usar o limite como valor é **conservador**, porque o tempo real é ≥ 120 s, então o speedup calculado é um **limite inferior** do verdadeiro;
- os timeouts são contados por célula (`n_timeout`) e relatados em todas as tabelas de resultados.

Uma consulta que der timeout nas 3 rodadas do piloto entra em `censored_queries`. Na coleta completa, ela roda só nas primeiras `reps_censored_full` (3) rodadas, para não gastar horas medindo um valor que já se sabe ser o limite.

## 6. Plano estatístico (fixo)

1. **Por item** (célula `sf × item`), três comparações:
   - **C1** sqlite × duckdb_t4 (principal);
   - **C2** sqlite × duckdb_t1 (efeito do motor colunar);
   - **C3** duckdb_t1 × duckdb_t4 (efeito do paralelismo).

   Para cada uma:
   - Shapiro-Wilk em `log(elapsed_ms)` nos dois grupos;
   - se ambos tiverem p ≥ 0,05, **t de Welch em `log`**; senão, **Mann-Whitney U** bilateral;
   - com n < 3 ou variância zero, o teste é marcado como "insuficiente";
   - **Holm** dentro de cada família (C1, C2 ou C3, por `sf`), com α = 0,05;
   - efeito por **Cliff's δ**, com os limiares de Romano: |δ| < 0,147 desprezível, < 0,33 pequeno, < 0,474 médio, resto grande;
   - **speedup** = mediana(a) / mediana(b), com IC 95% por bootstrap (5000 reamostragens, `seed` 20262).
2. **Entre consultas** (hipótese principal, por `sf`):
   - **média geométrica do speedup** nas 22 consultas, com IC 95% por bootstrap sobre as consultas;
   - **Wilcoxon signed-rank** pareado nas medianas por consulta (n = 22), aplicado em `log speedup_i`.

   A média é geométrica porque o speedup é uma razão: a média aritmética de razões depende de qual banco está no numerador e é puxada por valores extremos.
3. **OLTP:** o mesmo procedimento do item 1 para `ops_sec` e `p99_ms`, por operação.
4. **Volume (H₅):** comparação descritiva dos IC 95% do speedup em sf 0,1 e sf 1.
5. **Memória (Q5):** descritiva (mediana, IQR) de `peak_rss_mb` por engine × sf × workload.

**Por que esses testes:** os tempos de execução são positivos e assimétricos à direita, perto de log-normais. Por isso o t de Welch é aplicado em `log`, onde vira uma comparação de médias geométricas. O Welch não assume variâncias iguais, o que importa porque o DuckDB paralelo tende a ter menos dispersão. Quando a normalidade do log falha (bimodalidade por cache, timeouts no limite), o Mann-Whitney não depende de forma de distribuição. A escala de razão permite todas essas operações (ver [02](02-gqm-hipoteses.md)).

## 7. Critérios de decisão do piloto

O piloto (3 rodadas) serve para decidir o tamanho da coleta completa. As decisões são registradas em `05-piloto.md` e no `config.yaml`, **antes** da coleta completa:

1. **Tamanho da amostra:** para cada célula de C1, simular o poder de Mann-Whitney com n = 10, reamostrando o piloto (2000 simulações, α = 0,05) e deslocando para um efeito de δ = 0,33 (médio). Se o poder for **< 0,8 em mais de 20% das células**, aumentar `repetitions.full`.
2. **Censura:** consulta que der timeout nas **3** rodadas do piloto (em algum engine/sf) vai para `censored_queries`.
3. **Duração:** estimar a duração da coleta completa a partir da soma dos tempos do piloto, escalada pelo número de rodadas. Se passar de uma noite, priorizar e registrar o motivo.
4. **Qualidade:** o piloto só é aceito se `validate` não devolver nenhum **problema**. Os avisos de tendência levam a revisar as condições da máquina antes da coleta completa.
