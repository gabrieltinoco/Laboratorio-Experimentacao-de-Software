# Convenções do projeto — LAB05 (DuckDB × SQLite)

## 1. Planejamento oficial

O planejamento oficial é [`docs/planejamento.md`](planejamento.md). Assinaturas de funções, contratos de dados (`bench/config.yaml`, `results.csv`) e o plano estatístico seguem o que está lá. Mudanças no plano só entram por commit no próprio `planejamento.md`, com justificativa.

> A raiz do projeto é a pasta `Laboratorio05/` do repositório da disciplina. Na árvore do planejamento ela aparece como `lab05-duckdb-sqlite/`.

## 2. Restrições globais

- Não usar repositórios públicos do GitHub como objeto de pesquisa (mineração de commits/issues/PRs ou análise de código-fonte). O objeto é o **software em funcionamento**: DuckDB e SQLite executando consultas.
- Carga **apenas no ambiente do grupo**. Nenhum sistema de terceiros é medido.
- Não coletar dados pessoais. O TPC-H é sintético.
- Cada número de impacto ou critério tem **link + data de acesso** (`docs/impacto/fontes.yaml`).
- Versões estáveis mantidas, fixadas no `requirements.lock`. Cada run registra `duckdb.__version__` e `apsw.sqlitelibversion()`.
- Apresentação de **10 minutos**. Documento e apresentação em formato livre.
- Pontuação: S01 = 5, S02 = 5, S03 = 5, Final = 5 (total 20).
- O estudo é classificado nas **7 categorias** (natureza, objetivos, abordagem, procedimentos, tempo, controle, nível de evidência), cada uma com justificativa.
- Ameaças à validade dos **4 tipos** (conclusão, interna, construto, externa), cada uma com mitigação.
- A análise respeita a **escala** de cada métrica.
- Os bancos gerados (`data/db/`) **não** vão para o git. São regenerados de forma determinística por `make data`, e o `data/manifest.json` guarda os hashes.

## 3. Dados brutos são imutáveis

**Nunca edite `data/raw/`.** Um bloco inválido é apagado inteiro (o JSON) e rodado de novo, e o fato é registrado em `docs/05-piloto.md`. Toda transformação gera arquivos novos em `data/processed/`.

## 4. Testes

TDD com `pytest`: teste falhando → implementação → teste passando. Rode `make test` (ou `python -m pytest`) **antes de cada commit**.

## 5. Divisão do trabalho

Cada integrante executa só as suas tarefas (`A-*` ou `B-*`) e marca os checkboxes no `planejamento.md` ao concluir. Uma tarefa de B só começa quando todas as tarefas de A da mesma sprint estão concluídas.

## 6. Commits

- Cada integrante faz `git add` / `git commit` / `git push` **com a própria conta**, ao fim de cada tarefa.
- Mensagem: `tipo(escopo): descrição`, com o número da issue do Kanban (ex.: `docs: GQM, hipóteses e design (#12)`).
  - Tipos: `feat`, `fix`, `docs`, `test`, `chore`, `refactor`, `data`.
  - Escopos usuais: `bench`, `analysis`, `impact`, `dashboard`, `infra`.
- Sem trailers de coautoria (`Co-Authored-By`). O autor de todo commit é um dos integrantes.
- Ambiente local:

  ```bash
  python -m venv .venv
  .venv/Scripts/activate      # Windows (Git Bash) | source .venv/bin/activate no Linux/macOS
  pip install -r requirements.lock
  pip install -e .[dev] --no-deps
  ```
