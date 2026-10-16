# Dicionário de dados

Arquivos gerados por `python -m pipeline --config config.yaml` nesta pasta. Todos são regenerados a partir do cache (`cache/`): rodar o comando de novo com o cache completo não faz chamadas novas à API.

Convenções:

- **Janela de observação:** 2025-10-01 a 2026-09-30, inclusive (365 dias, ≈ 52,14 semanas), definida em `config.yaml`.
- **Datas:** ISO 8601 em UTC, como a API devolve (`2026-03-15T12:00:00Z`).
- **Release principal:** release com `draft = false` e `prerelease = false`. É a unidade de deploy da definição de referência.
- **Run válido:** workflow run com `conclusion` em `success` (sucesso) ou `failure`, `timed_out`, `startup_failure` (falha). Os demais valores são ignorados.
- **Célula vazia:** a métrica não pode ser calculada para aquele repositório (ex.: lead time sem nenhuma release com release anterior).

## `repositorios.csv`

Dataset final, com uma linha por repositório da amostra, ordenado por `repositorio`.

### Metadados

| Coluna | Tipo | Unidade | Origem / fórmula |
|---|---|---|---|
| `repositorio` | texto | — | `full_name` da busca (`/search/repositories`), no formato `dono/nome` |
| `url` | texto | — | `html_url` da busca |
| `estrelas` | inteiro | estrelas | `stargazers_count` da busca, no momento da coleta |
| `linguagem` | texto | — | `language` da busca (linguagem principal detectada pelo GitHub); vazio se não houver |
| `default_branch` | texto | — | `default_branch` da busca; único branch considerado nos workflow runs |
| `criado_em` | data/hora | UTC | `created_at` da busca |
| `idade_anos` | decimal | anos | (fim da janela − `criado_em`) ÷ 365,25, com 2 casas |
| `contribuidores` | inteiro | pessoas | número da última página de `/contributors?per_page=1&anon=true` (header `Link`); inclui contribuidores anônimos. Vazio quando a API recusa a listagem (HTTP 403 em históricos muito grandes) |
| `workflows` | inteiro | workflows | `total_count` de `/actions/workflows` |

### Volume coletado

| Coluna | Tipo | Unidade | Origem / fórmula |
|---|---|---|---|
| `releases_na_janela` | inteiro | releases | releases principais com `published_at` na janela |
| `releases_comparadas` | inteiro | releases | releases da janela com release principal anterior e `compare` disponível; são as que entram no lead time |
| `compare_404` | inteiro | releases | releases ignoradas no lead time porque `/compare/{anterior}...{release}` ficou indisponível: 404 (tag apagada ou reescrita) ou 422 (diff grande demais para a API gerar) |
| `workflow_runs_validos` | inteiro | runs | runs válidos do `default_branch` com `event = push` criados na janela |
| `meses_no_teto_de_runs` | inteiro | meses | meses em que a consulta mensal de `/actions/runs` atingiu 1.000 resultados; nesses meses a contagem pode estar truncada |

### Métricas DORA

| Coluna | Tipo | Unidade | Origem / fórmula | RQ |
|---|---|---|---|---|
| `deploy_freq_semana` | decimal | releases/semana | `releases_na_janela` ÷ (dias da janela ÷ 7) | 01 |
| `lead_time_release_dias` | decimal | dias | variante (a): para cada release comparada, `published_at` − `commit.author.date` do commit mais antigo incluído nela; valor do repositório = mediana entre as releases | 02 |
| `lead_time_commit_dias` | decimal | dias | variante (b): `published_at` da release − `commit.author.date` de cada commit incluído; valor do repositório = mediana de todos os commits de todas as releases comparadas | 02 |
| `cfr_ci` | decimal | proporção (0–1) | CFR (a), proxy de CI: runs com falha ÷ runs válidos | 03 |
| `recuperacao_horas` | decimal | horas | por workflow, episódio = da primeira falha após um sucesso (`run_started_at`) até o fim do próximo sucesso do mesmo workflow (`updated_at`); valor do repositório = mediana dos episódios encerrados de todos os workflows | 04 |
| `episodios_falha` | inteiro | episódios | episódios de falha, encerrados ou censurados | 04 |
| `episodios_censurados` | inteiro | episódios | episódios sem sucesso posterior dentro da janela | 04 |
| `proporcao_censurados` | decimal | proporção (0–1) | `episodios_censurados` ÷ `episodios_falha`; vazio sem episódios | 04 |

### Classificação DORA de referência (C1)

Combinação C1: release principal como deploy, lead time (a) e CFR (a). Cortes da tabela de referência do enunciado (seção 5, RQ 07).

| Coluna | Tipo | Valores | Origem / fórmula |
|---|---|---|---|
| `categoria_frequencia` | categoria | Elite, High, Medium, Low | `deploy_freq_semana`: ≥ 7; ≥ 1; ≥ 1 por mês (1 ÷ 4,345 por semana); abaixo disso |
| `categoria_lead_time` | categoria | Elite, High, Medium, Low | `lead_time_release_dias`: < 1; < 7; < 30; ≥ 30 |
| `categoria_cfr` | categoria | Elite, High, Medium, Low | `cfr_ci`: ≤ 0,15; ≤ 0,30; ≤ 0,45; > 0,45 |
| `categoria_recuperacao` | categoria | Elite, High, Medium, Low | `recuperacao_horas`: < 1; < 24; < 168; ≥ 168 |
| `categoria_geral` | categoria | Elite, High, Medium, Low | Elite = 4, High = 3, Medium = 2, Low = 1; mediana dos quatro pontos, arredondada para baixo. Vazia se alguma das quatro categorias estiver vazia |

## `metadados.csv`

Mesmas colunas da seção [Metadados](#metadados), só para os repositórios da amostra, sem as métricas.

## `funil.csv`

Uma linha por etapa da seleção, na ordem em que as etapas são aplicadas.

| Coluna | Tipo | Unidade | Descrição |
|---|---|---|---|
| `etapa` | texto | — | `encontrados na busca` (soma de `total_count` das faixas de estrelas), `candidatos coletados` (únicos acessíveis, até 1.000 por faixa), `candidatos avaliados`, `com GitHub Actions`, `metadados coletados`, `mínimo de releases e workflow runs` |
| `repositorios` | inteiro | repositórios | quantos restam ao fim da etapa |
| `descartados` | inteiro | repositórios | quantos saíram nesta etapa |
| `motivos` | texto | — | motivos agregados, no formato `motivo (quantidade)`, separados por `;` |

## `descartes.csv`

Um repositório descartado por linha.

| Coluna | Tipo | Descrição |
|---|---|---|
| `repositorio` | texto | `dono/nome` |
| `etapa` | texto | etapa do funil em que saiu (mesmos nomes de `funil.csv`) |
| `motivo` | texto | ex.: `sem workflows`, `erro ao listar workflows (HTTP 404)`, `3 releases válidas (mínimo 5)`, `12 workflow runs válidos (mínimo 50)` |

## Arquivos de coleta (`.jsonl`)

Um objeto JSON por linha, sempre com o campo `repositorio`. Só contêm repositórios da amostra.

### `releases.jsonl`

Releases publicadas na janela (inclusive pré-releases), drafts criados na janela e a última release principal anterior ao início da janela.

| Campo | Tipo | Origem |
|---|---|---|
| `id`, `tag_name`, `name`, `body`, `html_url` | — | campos homônimos de `/releases` |
| `draft`, `prerelease` | booleano | campos homônimos de `/releases` |
| `published_at`, `created_at` | data/hora | campos homônimos de `/releases`; drafts podem ter `published_at` vazio |

### `commits_entre_releases.jsonl`

Uma linha por release principal da janela comparada com a release principal anterior.

| Campo | Tipo | Origem |
|---|---|---|
| `tag_anterior`, `tag_release` | texto | `base` e `head` de `/compare/{base}...{head}` |
| `published_at` | data/hora | publicação da release `tag_release` |
| `commits` | lista | todos os commits do `compare` (paginado), cada um com `sha`, `author_date` (`commit.author.date`), `message` e `html_url` |

### `compare_404.jsonl`

| Campo | Tipo | Descrição |
|---|---|---|
| `tag_anterior`, `tag_release` | texto | comparação indisponível |
| `status` | inteiro | código HTTP: 404 (tag apagada ou reescrita) ou 422 (diff grande demais) |

### `workflow_runs.jsonl`

Runs do `default_branch` com `event = push`, consultados mês a mês na janela. Inclui runs com `conclusion` ignorada, para auditoria.

| Campo | Tipo | Origem |
|---|---|---|
| `id`, `name`, `workflow_id`, `head_branch`, `head_sha`, `event`, `status`, `conclusion`, `html_url` | — | campos homônimos de `/actions/runs` |
| `created_at`, `run_started_at`, `updated_at` | data/hora | campos homônimos; `run_started_at` marca o início de uma falha e `updated_at` o fim de um sucesso |

## `coleta_resumo.json`

Objeto indexado por `repositorio`, com `releases_validas_na_janela`, `workflow_runs_coletadas` (todos os runs), `workflow_runs_validas`, `compare_404`, `workflow_runs_por_mes` (`total_count` informado pela API em cada mês `AAAA-MM`) e `meses_no_teto` (lista dos meses com 1.000 resultados ou mais).

## Validação manual (`validacao/`)

Gerados pelos scripts de `validacao/` (ver [PROTOCOLO.md](../validacao/PROTOCOLO.md)).

| Arquivo | Colunas | Descrição |
|---|---|---|
| `amostra_ouro.csv` | `repositorio`, `tag_name`, `publicada_em`, `tag_anterior`, `link_release`, `link_commits` | 60 repositórios e 5 releases principais da janela por repositório, sorteados com semente 42 |
| `rotulos_<avaliador>.xlsx` | aba `repositorios`: `tipo_projeto`, `entregas_reais`, `observacoes`; aba `releases`: `corretiva`, `observacoes` | rótulos independentes de cada avaliador |
| `concordancia.csv` | `dimensao`, `itens`, `concordancia_observada`, `kappa_cohen`, `kappa_fleiss`, `interpretacao` | concordância por dimensão; interpretação de Landis & Koch sobre o kappa de Cohen |
| `divergencias.csv` | `dimensao`, `repositorio`, `tag_name`, `rotulo_<avaliador>`…, `rotulo_consenso`, `motivo` | itens divergentes e a decisão da reunião de consenso |
| `consenso_repositorios.csv` | `repositorio`, `tipo_projeto`, `entregas_reais` | rótulo final por repositório (fator *tipo do projeto* da RQ 06) |
| `consenso_releases.csv` | `repositorio`, `tag_name`, `corretiva` | rótulo final por release (referência para P/R/F1 da heurística) |

Valores permitidos: `tipo_projeto` ∈ {biblioteca/framework, aplicação/serviço, ferramenta CLI, outro}; `entregas_reais` ∈ {sim, não, incerto}; `corretiva` ∈ {sim, não}.
