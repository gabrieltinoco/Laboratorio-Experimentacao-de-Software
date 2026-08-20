# Reproducibilidade e integridade dos dados do Lab01

Documento de apoio da Issue **Garantir reprodutibilidade e integridade dos dados do Lab01**.

## Objetivo

Registrar como recriar a coleta, validar a integridade do CSV dos 1.000 repositórios e conferir casos extremos sem editar os dados manualmente.

## Ambiente

- Sistema usado na entrega: Windows.
- Python recomendado: 3.10 ou superior.
- Dependência externa: `requests`, declarada em `src/requirements.txt`.
- Fonte: API GraphQL v4 do GitHub.
- Recorte: busca `stars:>1 sort:stars-desc`, tipo `REPOSITORY`, com 1.000 resultados.
- Arquivo de entrada das validações: `data/repositorios_top1000.csv`.

## Como reproduzir

No PowerShell, a partir da raiz do repositório:

```powershell
cd Laboratorio01
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r src\requirements.txt
```

A coleta exige um token público do GitHub na variável de ambiente. O token não deve ser commitado:

```powershell
$env:GITHUB_TOKEN = "cole-o-apenas-no-terminal"
python src\fetch_repos.py
```

A coleta grava `data/repositorios_top1000.csv`. Para validar as RQs 01 e 02 usando explicitamente o CSV de 1000 linhas:

```powershell
python src\rq01_rq02.py data\repositorios_top1000.csv
```

As demais validações disponíveis são:

```powershell
python src\validate_sample_rq03_rq04.py
python src\validate_sample.py
python src\rq09_cadencia_releases.py
```

A consulta não deve ser executada sem necessidade, pois gera uma nova fotografia do ranking. Para reproduzir somente a análise desta entrega, use o CSV versionado e não rode `fetch_repos.py`.

## Critérios de integridade

O validador de RQ01/RQ02 verifica:

- existência e escolha das colunas de identificação, data de criação e PRs aceitas;
- valores ausentes ou inválidos em `created_at` e `pull_requests_aceitas`;
- datas que podem ser convertidas e idade calculada;
- valores negativos ou não numéricos de PRs aceitas;
- quantidade de linhas analisadas;
- identificadores vazios;
- nomes de repositório duplicados;
- quartis, IQR e outliers pelo critério de Tukey;
- distribuição por faixas e os principais valores extremos.

Para o CSV atual, o resultado esperado é:

| Verificação | Resultado |
|---|---:|
| Linhas de dados | 1000 |
| Nomes distintos | 1000 |
| Nomes duplicados | 0 |
| `created_at` ausente/inválido | 0 (0,0%) |
| `pull_requests_aceitas` ausente/inválido | 0 (0,0%) |
| Outliers de idade pelo critério de Tukey | 0 |
| Outliers de PRs pelo critério de Tukey | 124 (12,4%) |

Outliers são mantidos na base. Eles são evidências da distribuição e não devem ser removidos sem justificativa metodológica.

## Dicionário de dados

| Coluna | Tipo | Significado | Uso |
|---|---|---|---|
| `repositorio` | texto | Nome completo no formato `owner/name` | Identificação e auditoria |
| `created_at` | data ISO 8601 | Data de criação do repositório | RQ01 e RQ09 |
| `estrelas` | inteiro | Quantidade de estrelas no momento da coleta | Recorte e análises complementares |
| `linguagem_primaria` | texto | Linguagem primária informada pelo GitHub | RQ05 e RQ07 |
| `licenca` | texto | Identificador SPDX ou ausência de licença | RQ08 |
| `issues_total` | inteiro | Total de issues do repositório | RQ06 |
| `issues_fechadas` | inteiro | Total de issues com estado `CLOSED` | RQ06 |
| `percentual_issues_fechadas` | decimal | Razão entre issues fechadas e issues totais, entre 0 e 1 | RQ06 |
| `pull_requests_aceitas` | inteiro | Total de pull requests com estado `MERGED` | RQ02 e RQ07 |
| `total_releases` | inteiro | Total de releases retornado pela API | RQ03, RQ07 e RQ09 |
| `ultima_atualizacao` | data ISO 8601 | Valor GraphQL `updatedAt` | RQ04 |
| `dias_desde_ultima_atualizacao` | inteiro | Dias calculados desde `updatedAt` no momento da coleta | RQ04 |
| `ultimo_push` | data ISO 8601 | Valor GraphQL `pushedAt` | Leitura complementar da RQ04 e RQ09 |
| `dias_desde_ultimo_push` | inteiro | Dias calculados desde `pushedAt` no momento da coleta | RQ04 e RQ09 |

## Casos extremos observados

Tabela extraída do CSV atual, sem remoção de registros:

| Tipo | Repositório | Valor | Interpretação |
|---|---|---:|---|
| Mais antigo | `rails/rails` | `2008-04-11` | Maior idade observada |
| Mais antigo | `git/git` | `2008-07-23` | Projeto histórico e maduro |
| Mais novo | `deepseek-ai/deepseek-harness` | `2026-08-13` | Projeto criado durante o recorte temporal |
| Mais novo | `DietrichGebert/ponytail` | `2026-06-12` | Projeto recente no top 1000 |
| Maior número de PRs aceitas | `firstcontributions/first-contributions` | 103354 | Outlier superior de RQ02 |
| Maior número de PRs aceitas | `llvm/llvm-project` | 97111 | Outlier superior de RQ02 |
| Maior número de PRs aceitas | `elastic/elasticsearch` | 95532 | Outlier superior de RQ02 |
| Zero PRs aceitas | `awesome-selfhosted/awesome-selfhosted` | 0 | Outlier inferior/ausência de contribuição merged |
| Zero PRs aceitas | `torvalds/linux` | 0 | Deve ser interpretado com cautela: a métrica conta PRs GitHub merged |

Os cinco maiores valores de RQ02 identificados pelo critério de Tukey foram `firstcontributions/first-contributions`, `llvm/llvm-project`, `elastic/elasticsearch`, `getsentry/sentry` e `home-assistant/core`. A média não deve ser usada sozinha, pois esses valores elevam fortemente a cauda da distribuição; a mediana é a estatística central principal.

## Limitações e cuidados

- `pull_requests_aceitas` conta PRs merged de qualquer autor, inclusive mantenedores; é uma aproximação de contribuição externa.
- O ranking por estrelas é uma fotografia e muda com o tempo.
- `total_releases` pode estar limitado pelo comportamento da API.
- Repositórios de listas, roteiros e material didático podem aparecer entre os mais estrelados e não representar software tradicional.
- Os valores derivados de dias dependem do momento da coleta.
- O token do GitHub é segredo operacional e não faz parte do repositório.

## Evidência da execução

A Issue deve anexar ou vincular a saída do comando abaixo no fechamento da tarefa:

```powershell
python src\rq01_rq02.py data\repositorios_top1000.csv > validacao_rq01_rq02.txt
```

O arquivo `validacao_rq01_rq02.txt` é uma evidência local da execução e pode ser anexado à Issue, mas não precisa ser versionado se o grupo preferir manter apenas o script e este documento.
