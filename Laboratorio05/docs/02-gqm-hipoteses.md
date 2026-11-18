# 02 — GQM, hipóteses, variáveis e design

## 1. Pergunta de pesquisa e caminho

> *Em consultas analíticas, quanto o DuckDB é mais rápido que o SQLite, essa vantagem vem do motor colunar ou só do paralelismo, e ela se inverte em operações transacionais (leitura e escrita de uma linha)?*

**Caminho escolhido:** *rodar o software no ambiente do grupo*. Os dois bancos, nas versões estáveis de produção ([01](01-software-criterios.md)), executam uma carga padronizada numa máquina controlada. Para estimar o impacto (Sprint 3), o resultado medido é combinado com dados públicos de adoção.

## 2. Objetivo (template GQM de Basili)

| Elemento | Valor |
|---|---|
| **Analisar** | DuckDB e SQLite |
| **com o propósito de** | comparar |
| **com respeito ao** | tempo de resposta e à vazão |
| **do ponto de vista de** | desenvolvedores e analistas de dados que escolhem um banco embarcado |
| **no contexto de** | um único computador, com cargas analíticas (TPC-H) e transacionais, em 2 tamanhos de dados (sf 0,1 ≈ 100 MB e sf 1 ≈ 1 GB) |

## 3. Perguntas e métricas

| Pergunta | Métrica(s) | Como responde |
|---|---|---|
| **Q1.** Quanto tempo as consultas analíticas levam em cada banco? | `elapsed_ms` por consulta; speedup C1 (sqlite/duckdb_t4) | comparação por consulta e média geométrica do speedup nas 22 consultas |
| **Q2.** O ganho vem do motor colunar ou do paralelismo? | speedup C2 (sqlite/duckdb_t1) × speedup C3 (duckdb_t1/duckdb_t4) | C1 = C2 × C3, ou seja, o ganho total se decompõe em colunar × paralelismo |
| **Q3.** O ganho cresce com o volume de dados? | speedup C1 por `sf` | IC 95% do speedup em sf 0,1 × sf 1 |
| **Q4.** Como os bancos se saem em operações transacionais? | `ops_sec`, `p99_ms` (point_select, insert, update) | comparação por operação |
| **Q5.** Quanto de memória cada banco usa? | `peak_rss_mb` | descritiva por engine × sf × workload |

### Classificação das métricas

Todas as métricas medem o **produto** (o banco em execução) e um **atributo externo**, isto é, um comportamento observado durante a execução e não uma propriedade do código.

| Métrica | Entidade | Atributo | Direta/derivada | Escala | Estatísticas permitidas |
|---|---|---|---|---|---|
| `elapsed_ms` | produto (consulta executada) | tempo de resposta (externo) | direta | **razão** | todas: média, mediana, média geométrica, razões, testes paramétricos (em log) e não paramétricos |
| `ops_sec` | produto (carga OLTP) | vazão (externo) | derivada (`n_ops / tempo`) | **razão** | todas |
| `p99_ms` | produto (carga OLTP) | latência de cauda (externo) | derivada (percentil 99 das latências por operação) | **razão** | todas; usada com mediana/IQR entre rodadas |
| `peak_rss_mb` | produto (processo) | consumo de memória (externo) | direta | **razão** | todas |
| `rows_returned` | produto | tamanho do resultado | direta | **razão** (contagem) | usada só na checagem de correção |
| **speedup** | par de tratamentos | ganho relativo | **derivada** (mediana(a)/mediana(b)) | **razão** (adimensional) | razões e **média geométrica** (a média aritmética de razões é enviesada); IC por bootstrap |
| Cliff's δ | par de tratamentos | tamanho de efeito | derivada | intervalar em [-1, 1] | comparação com os limiares de Romano |
| `engine`, `workload`, `item` | — | fator / identificação | — | **nominal** | contagem, moda; definem os grupos |
| `sf` | — | volume de dados | — | razão, tratado como **fator de 2 níveis** | definem as células |

## 4. Hipóteses

Todas são bilaterais, com α = 0,05. O procedimento completo está em [04](04-plano-coleta-analise.md).

| # | H0 | H1 | Teste |
|---|---|---|---|
| **H₁** (principal) | a média geométrica do speedup sqlite/duckdb_t4 nas 22 consultas OLAP é 1 | é diferente de 1 | IC 95% bootstrap da média geométrica + Wilcoxon signed-rank pareado nas medianas por consulta (n = 22), por `sf` |
| **H₂** (colunar) | speedup sqlite/duckdb_t1 = 1 | ≠ 1 | igual a H₁, com C2 |
| **H₃** (paralelismo) | speedup duckdb_t1/duckdb_t4 = 1 | ≠ 1 | igual a H₁, com C3 |
| **H₄** (OLTP) | `ops_sec` do SQLite = `ops_sec` do DuckDB (por operação, por `sf`) | ≠ | Welch em log ou Mann-Whitney (por Shapiro-Wilk), Holm, Cliff's δ |
| **H₅** (volume) | o speedup C1 não muda entre sf 0,1 e sf 1 | muda | comparação **descritiva** dos IC 95% (com só 2 níveis de `sf`, não fazemos teste formal de interação) |

Cada consulta também tem a sua própria comparação C1, C2 e C3 (Welch em log ou Mann-Whitney, com Holm por família e por `sf`). É isso que mostra **quais** consultas sustentam o resultado agregado.

## 5. Variáveis

| Tipo | Variáveis |
|---|---|
| **Independentes (fatores)** | `engine` ∈ {sqlite, duckdb_t1, duckdb_t4}; `sf` ∈ {0,1; 1}; `workload` ∈ {olap, oltp} |
| **Dependentes** | `elapsed_ms`, `ops_sec`, `p99_ms`, `peak_rss_mb` (e o speedup derivado) |
| **Fixas (controladas)** | `sqlite_settings` (WAL, synchronous=NORMAL, cache de 256 MiB, índices nas PKs e FKs); `duckdb_settings` (memory_limit 4 GB); `limits` do container (4 CPUs, 8 GB); a mesma máquina, a mesma imagem Docker e as mesmas versões (`requirements.lock`); os mesmos dados (gerados com `seed` fixa, hash no manifest); `timeout_ms` = 120 s |
| **De confusão** | cache de páginas do SO (quente × frio), temperatura e *throttling* da CPU, processos em segundo plano, ordem de execução, consulta traduzida de forma diferente entre os dialetos |

**Mitigação das variáveis de confusão:**

- cada bloco roda num container novo, com o mesmo aquecimento (um `count(*)` por tabela, sem medir), o que deixa todos os tratamentos com cache igualmente quente;
- a ordem dos blocos e a ordem dos itens dentro do bloco são sorteadas (`seed`);
- a coleta roda com a máquina na tomada, em modo de alto desempenho, sem outros programas;
- um teste de tendência (Spearman entre `order` e `elapsed_ms`) detecta deriva;
- o `result_hash` precisa ser igual nos dois bancos, o que prova que as consultas fazem a mesma coisa.

### Por que existe o tratamento `duckdb_t1`

O SQLite executa cada consulta em **uma única thread**. O DuckDB, por padrão, usa todos os núcleos. Comparar só sqlite × duckdb_t4 mistura dois efeitos:

1. o **motor**: armazenamento colunar, execução vetorizada, compressão;
2. o **paralelismo**: 4 threads × 1.

O `duckdb_t1` é o DuckDB limitado a 1 thread, com o mesmo número de núcleos do SQLite. Assim:

- **C2** (sqlite × duckdb_t1) mede só o efeito do motor;
- **C3** (duckdb_t1 × duckdb_t4) mede só o efeito do paralelismo;
- como os speedups se multiplicam (C1 = C2 × C3), dá para dizer **quanto** do ganho total vem de cada fonte (Q2).

Sem esse tratamento de controle não seria possível responder à segunda parte da pergunta de pesquisa.

## 6. Design experimental

- **Fatorial completo:** 3 `engine` × 2 `sf` × 2 `workload`. Os itens são 22 consultas (OLAP) e 3 operações (OLTP).
- **Unidade de execução = bloco** `(engine, sf, workload, round)`, rodado num container novo. Os itens do bloco rodam em ordem sorteada, uma vez cada.
- **Repetições:** 3 rodadas no piloto e 10 na coleta completa (o número final é decidido pelo poder simulado no piloto, ver [04](04-plano-coleta-analise.md)).
- **Medidas repetidas por item:** a mesma consulta é medida em todos os tratamentos. Isso permite a análise **pareada por consulta** entre as consultas (Wilcoxon signed-rank).
- **Aleatorização:** a ordem dos blocos e a ordem dos itens vêm de `random.Random(seed)`, o que torna a agenda reprodutível.

## 7. Armadilhas de medição

**Lei de Goodhart: "quando uma medida vira meta, deixa de ser uma boa medida".** Um benchmark é fácil de "jogar". Deixar o SQLite **sem índices** aumentaria artificialmente a vantagem do DuckDB, e configurar o SQLite com `synchronous=OFF` ou banco em memória faria o contrário. Para não otimizar o número em vez da pergunta:

- o SQLite recebe PKs e índices nas FKs do TPC-H, com `ANALYZE`, como em produção;
- os dois usam configurações recomendadas e documentadas (WAL + NORMAL; `memory_limit` comparável ao cache do SQLite);
- não há ajuste por consulta (*query hints*, reescrita específica);
- a configuração é fixada **antes** do piloto e não muda depois de ver os resultados.

**Campbell / falácia de McNamara: "o que não é medido não deixa de importar".** Este estudo **não mede**, e as conclusões não devem ser lidas como se medissem:

- concorrência entre vários processos ou escritores, onde o *locking* do SQLite e o modelo do DuckDB diferem muito;
- durabilidade e recuperação após falha;
- tamanho do binário e consumo em dispositivos pequenos (ARM, celular), onde o SQLite domina;
- facilidade de uso, ecossistema, maturidade e estabilidade de formato de arquivo;
- tempo de carga dos dados e custo de manter índices.

**Carga sintética:** o TPC-H é um benchmark **sintético** de apoio à decisão. A distribuição dos dados é uniforme e as consultas são fixas. Ele representa bem "agregações sobre tabelas grandes", mas não representa uma carga real específica. O OLTP daqui (point select, insert e update por chave) é uma simplificação deliberada do uso transacional típico de um app.
