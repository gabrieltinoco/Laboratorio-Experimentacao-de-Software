# Lab03 — Mineração de Métricas DORA

Pipeline que coleta dados públicos de repositórios populares do GitHub que usam GitHub Actions e calcula, a partir deles, aproximações das quatro métricas DORA (frequência de deploy, lead time, change failure rate e tempo de recuperação). O enunciado está em [03 - Mineração de Métricas DORA.md](03%20-%20Minera%C3%A7%C3%A3o%20de%20M%C3%A9tricas%20DORA.md).

## Pré-requisitos

- Python 3.12 ou superior
- Um token do GitHub ([classic ou fine-grained](https://github.com/settings/tokens)) só com acesso de leitura a repositórios públicos

## Instalação

```bash
cd Laboratorio03
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Token do GitHub

O token é lido **somente** da variável de ambiente `GITHUB_TOKEN` e nunca é gravado no repositório nem no cache.

```bash
export GITHUB_TOKEN=ghp_...            # Linux/macOS
$env:GITHUB_TOKEN = "ghp_..."          # Windows PowerShell
```

## Execução

```bash
python -m pipeline --config config.yaml
```

O comando roda, em sequência, a seleção com o funil, a coleta de releases, commits entre releases e workflow runs, e o cálculo das métricas. O resultado final é `dados/repositorios.csv`, com uma linha por repositório da amostra. A amostra tem 306 repositórios (`selecao.max_repositorios`), acima do mínimo de 300 exigido após os filtros. A primeira execução leva várias horas por causa do rate limit. Se for interrompida, rode o mesmo comando de novo: o cache continua de onde parou.

Todos os parâmetros (janela de observação, faixas de estrelas da busca, critério mínimo de inclusão, tentativas e backoff) ficam em [config.yaml](config.yaml).

### Subamostra (replicação cruzada)

Para rodar o pipeline só sobre uma lista de repositórios, sem a busca, e gravar as saídas em outra pasta (o `dados/` original fica intacto para comparação):

```bash
python -m pipeline --config config.yaml --repos replicacao/subamostra_30.txt --saida dados_replicacao
```

O arquivo tem um `dono/nome` por linha; linhas vazias e iniciadas por `#` são ignoradas. [replicacao/subamostra_30.txt](replicacao/subamostra_30.txt) traz 30 repositórios sorteados de `dados/repositorios.csv` com `sample(n=30, random_state=42)`. Os repositórios da lista passam pelos mesmos filtros (Actions e critério mínimo); os que não passam aparecem em `descartes.csv`. Com a lista de 30, a coleta leva de alguns minutos a cerca de uma hora, conforme o número de workflow runs e de commits entre releases dos repositórios.

### Seleção de repositórios e funil

Para rodar só a seleção e a coleta, sem calcular as métricas:

```bash
python -m pipeline.selecao --config config.yaml
```

1. **Busca fatiada:** uma consulta a `/search/repositories` por faixa de estrelas de `selecao.faixas_estrelas`, com `pushed:>=<início da janela> archived:false`. Cada consulta devolve no máximo 1.000 resultados. Se uma faixa tiver mais, o log avisa e a faixa pode ser dividida no `config.yaml`. Repositórios repetidos entre faixas entram uma vez só.
2. **Ordem de avaliação:** os candidatos são embaralhados com `selecao.semente`, para a amostra não ficar só com os mais populares, e avaliados nessa ordem até a amostra chegar a `selecao.max_repositorios`.
3. **GitHub Actions:** repositórios com `total_count = 0` em `/actions/workflows` são descartados antes de qualquer outra chamada.
4. **Metadados:** estrelas, linguagem, `default_branch`, data de criação, idade em anos no fim da janela e número de contribuidores (`/contributors?per_page=1&anon=true` + header `Link`). Quando o GitHub se recusa a listar os contribuidores (repositório grande demais), o valor fica vazio e o repositório continua na amostra.

Erros 4xx descartam o repositório com o código HTTP como motivo. Falhas de rede que continuam depois de todas as tentativas interrompem a coleta, para não virar descarte. Basta rodar de novo para continuar.

A seleção também coleta releases publicadas e workflow runs do branch padrão
disparados por `push`. Só entram na amostra repositórios com ao menos o mínimo
configurado de releases publicadas e runs com conclusão `success`, `failure`,
`timed_out` ou `startup_failure`. Releases prévias e drafts são preservados nos
dados, mas não contam para o critério principal. Os workflow runs são consultados
por mês; meses com 1.000 resultados ou mais geram um alerta porque a API pode
truncar a consulta. Comparações de releases são paginadas; respostas 404 (tag
apagada) e 422 (diff grande demais) são registradas sem interromper a coleta.
Listagens com mais de 10.000 itens param no teto da API, com um aviso no log.

Saídas em `dados/` (os `.jsonl` passam de 100 MB e ficam fora do git; rodar o pipeline com o cache os regenera):

| Arquivo | Conteúdo |
|---|---|
| `metadados.csv` | um repositório por linha: `repositorio`, `url`, `estrelas`, `linguagem`, `default_branch`, `criado_em`, `idade_anos`, `contribuidores`, `workflows` |
| `funil.csv` | quantos repositórios restam em cada etapa, quantos saíram e os motivos agregados |
| `descartes.csv` | cada repositório descartado, com etapa e motivo |
| `releases.jsonl` | releases coletadas na janela e release principal anterior |
| `tags.jsonl` | tags com commit a partir do início da janela e data `commit.author.date` do commit apontado (via GraphQL) |
| `commits_entre_releases.jsonl` | commits paginados de cada comparação, com `commit.author.date` |
| `compare_404.jsonl` | releases cujo endpoint `compare` retornou 404 ou 422 |
| `workflow_runs.jsonl` | runs do branch padrão e evento `push` |
| `coleta_resumo.json` | contagem de releases/runs válidos, 404 de compare e alertas mensais |
| `repositorios.csv` | metadados + métricas + classificação DORA (só no comando completo; ver abaixo) |

### Métricas por repositório (`repositorios.csv`)

O dicionário completo de todas as saídas (tipo, unidade e fórmula ou origem de cada coluna) está em [dados/DICIONARIO.md](dados/DICIONARIO.md). Resumo, além das colunas de `metadados.csv`:

| Coluna | Unidade | Origem |
|---|---|---|
| `releases_na_janela` | contagem | releases com `draft = false` e `prerelease = false` publicadas na janela |
| `releases_comparadas` | contagem | releases com release anterior e `compare` disponível (entram no lead time) |
| `compare_404` | contagem | releases ignoradas no lead time porque o `compare` retornou 404 ou 422 |
| `workflow_runs_validos` | contagem | runs com `conclusion` de sucesso ou falha |
| `meses_no_teto_de_runs` | contagem | meses em que a consulta de runs atingiu 1.000 resultados |
| `deploy_freq_semana` | releases/semana | `releases_na_janela` ÷ semanas da janela |
| `deploy_freq_com_prereleases_semana` | releases/semana | variante incluindo pré-releases publicadas, sem drafts |
| `deploy_freq_tags_semana` | tags/semana | tags cujo commit apontado tem `author_date` na janela ÷ semanas |
| `lead_time_release_dias` | dias | variante (a): mediana, entre as releases, de publicação − commit mais antigo |
| `lead_time_commit_dias` | dias | variante (b): mediana de publicação − `commit.author.date` de todos os commits |
| `cfr_ci` | proporção (0–1) | CFR (a): falhas ÷ (falhas + sucessos) dos workflow runs |
| `cfr_releases` | proporção (0–1) | CFR (b): releases principais seguidas por corretiva em até 7 dias ÷ releases avaliáveis |
| `releases_avaliadas_cfr` / `releases_falhas_cfr` / `releases_censuradas_cfr` | contagem | denominador, falhas e releases dos últimos 7 dias excluídas do CFR (b) |
| `releases_corretivas` / `rework_rate` | contagem / proporção (0–1) | RQ 08: releases marcadas como corretivas pela heurística e essa contagem ÷ `releases_na_janela` |
| `recuperacao_horas` | horas | mediana dos episódios de falha encerrados, por workflow |
| `episodios_falha` / `episodios_censurados` | contagem | episódios de falha e os que não terminaram na janela |
| `proporcao_censurados` | proporção (0–1) | `episodios_censurados` ÷ `episodios_falha` |
| `categoria_*` | Elite/High/Medium/Low | classificação de referência (C1) de frequência, lead time (a), CFR (a) e recuperação |
| `categoria_geral` | Elite/High/Medium/Low | mediana dos pontos das quatro categorias, arredondada para baixo; vazia se faltar alguma métrica |

### Validação manual (amostra-ouro)

Depois da coleta, com `dados/repositorios.csv` e `dados/releases.jsonl` prontos:

```bash
python -m validacao.gerar_planilha --config config.yaml   # sorteio + uma planilha por avaliador
# cada avaliador preenche validacao/rotulos_<avaliador>.xlsx, sem consultar o outro
python -m validacao.exportar_rotulos --planilha validacao/rotulos_avaliador_1.xlsx --saida validacao/rotulos_B.csv
python -m validacao.concordancia --config config.yaml     # kappa de Cohen/Fleiss + divergencias.csv
# reunião de consenso: preencher rotulo_consenso e motivo em validacao/divergencias.csv
python -m validacao.consenso --config config.yaml         # consenso_repositorios.csv e consenso_releases.csv
```

O CSV de entrega tem uma linha por release e repete nela os rótulos do
repositório (`tipo_projeto` e `entregas_reais`). A planilha XLSX permanece como
fonte para os scripts de concordância e consenso; o exportador valida todos os
rótulos antes de gravar o CSV.

Semente, tamanho da amostra e identificadores dos avaliadores ficam na seção `validacao` do [config.yaml](config.yaml). Critérios de rotulação e regras de desempate estão em [validacao/PROTOCOLO.md](validacao/PROTOCOLO.md).

Após a reunião de consenso, avalie e registre cada versão da heurística:

```bash
python -m validacao.avaliar_heuristica --config config.yaml --versao v1
```

O resultado é acrescentado a `validacao/avaliacao_heuristica.csv`; uma versão
já registrada não é sobrescrita. O comando requer
`validacao/consenso_releases.csv` produzido pelo consenso.

### Análises (Lab03S03)

Cada análise é um script que lê apenas `dados/repositorios.csv` e grava tabelas (`.csv` e `.md`) e figuras (`.png`) em `analise/saidas/`:

```bash
python -m analise.comum       # classificação DORA de referência (C1): classificacao_c1.csv
python -m analise.rq01_04     # mediana/IQR das métricas, censura, lead time (a) x (b), categorias C1
python -m analise.rq05_rq08   # Spearman frequência x CFR (a) e (b); rework rate x CFR (b)
python -m analise.rq06_rq07   # Kruskal-Wallis/Holm, tamanhos de efeito e sensibilidade C1/C2/C3
```

`analise/comum.py` também expõe `classificar(df, frequencia, lead_time, cfr)`, que classifica qualquer combinação de colunas (C2 e C3 da RQ 07). Todos aceitam `--dados` e `--saidas` para rodar sobre outro CSV, como o da replicação.

`analise.rq06_rq07` salva tabelas CSV/Markdown de Kruskal-Wallis com correção
de Holm, ε², Cliff's δ com magnitudes de Romano, categorias por repositório
nas combinações C1/C2/C3 e percentual de mudança/kappa ponderado linear. Os
resultados e a interpretação estão em
[`artigo/resultados_rq06_07.md`](artigo/resultados_rq06_07.md). O fator tipo
de projeto usa `validacao/consenso_repositorios.csv` quando o consenso existe;
enquanto houver divergências sem decisão, inclui apenas rótulos idênticos dos
dois avaliadores, deixando os demais fora dessa comparação.

### Cache e retomada

Cada resposta da API é salva em `cache/` (um JSON por requisição, agrupado por repositório em `cache/repos/<dono>__<repo>/`). Se a coleta for interrompida (rate limit, queda de rede, `Ctrl+C`), basta rodar o mesmo comando de novo: o que já está no cache não é pedido outra vez. Respostas 404/409/422/451 também ficam no cache, porque não mudam se repetidas; respostas 5xx e 403 não.

Para forçar uma coleta nova, apague a pasta `cache/`.

### Rate limit e erros

- Quando `X-RateLimit-Remaining` chega a 0, o cliente espera até `X-RateLimit-Reset`. No rate limit secundário, respeita `Retry-After`; sem nenhum desses headers, consulta `GET /rate_limit` (que não consome cota).
- Respostas 5xx e erros de rede são repetidos com backoff exponencial (1, 2, 4, 8 s), até `http.max_tentativas` tentativas.
- As tags são consultadas pela API GraphQL (`POST /graphql`), 100 por requisição e já com a data do commit apontado, com o mesmo cache, a mesma espera por cota e o mesmo backoff. A cota do GraphQL é separada da do REST.

### Comparação da replicação cruzada

Com os dois datasets disponíveis, compare métricas e categorias DORA por
repositório:

```bash
python -m replicacao.comparar --referencia dados/repositorios.csv --replicacao caminho/para/repositorios.csv --saida replicacao/resultado
```

O comando gera médias de diferenças absolutas e relativas, concordância das
classificações e arquivos detalhados para diferenças métricas, categorias e
repositórios ausentes em um dos datasets. A diferença relativa é
`(replicação - referência) / |referência|`; quando o valor de referência é
zero, ela fica indefinida e não entra na média relativa. Revise o relatório e
as diferenças com o grupo antes de abrir Issues no repositório replicado.

## Testes

```bash
pytest --cov=metricas --cov=pipeline --cov=validacao --cov=analise --cov-report=term-missing
```

O CI ([.github/workflows/lab03-testes.yml](../.github/workflows/lab03-testes.yml)) roda os testes a cada push que altere esta pasta e falha se a cobertura de `metricas/` ficar abaixo de 80%.

## Estrutura

```text
Laboratorio03/
├── config.yaml          # janela, filtros, caminhos
├── requirements.txt
├── pipeline/
│   ├── __main__.py      # python -m pipeline: executa todas as etapas
│   ├── http_client.py   # GET autenticado, paginação, cache, rate limit, backoff
│   ├── selecao.py       # busca fatiada, filtro de Actions, seleção da amostra
│   ├── metadados.py     # estrelas, linguagem, idade, contribuidores
│   ├── funil.py         # funil.csv e descartes.csv
│   ├── releases.py      # releases e commits entre releases
│   ├── tags.py          # tags e data do commit apontado (GraphQL)
│   ├── workflow_runs.py # runs segmentados por mês
│   ├── coleta.py        # critério mínimo e persistência da coleta
│   └── consolidacao.py  # métricas por repositório e repositorios.csv
├── metricas/            # funções puras de cálculo e classificação DORA
├── validacao/           # amostra-ouro: sorteio, planilhas, concordância, consenso, PROTOCOLO.md
├── analise/             # scripts da S03, reexecutáveis a partir de repositorios.csv
├── replicacao/          # subamostra para a replicação cruzada
├── tests/
├── artigo/              # hipóteses da introdução e seções incrementais
├── dados/               # CSVs finais + dicionário de dados
└── cache/               # respostas da API (fora do git)
```

### Uso do cliente HTTP

```python
from pipeline.http_client import GitHubClient, ErroGitHub

gh = GitHubClient(cache_dir="cache")                         # token vem de GITHUB_TOKEN
releases = gh.get_todos("/repos/pallets/flask/releases")     # todas as páginas
runs = gh.get_todos("/repos/pallets/flask/actions/runs",
                    {"event": "push", "branch": "main", "created": "2025-10-01..2025-10-31"},
                    chave="workflow_runs")
contribuidores = gh.contar("/repos/pallets/flask/contributors", {"anon": "true"})

try:
    gh.get_todos("/repos/o/r/compare/v1.0...v1.1", chave="commits")
except ErroGitHub as erro:
    if erro.status == 404:
        ...  # tag apagada: registrar e ignorar a release no lead time
```
