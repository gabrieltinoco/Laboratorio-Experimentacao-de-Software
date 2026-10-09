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

> O comando único é montado na Issue #6. Até lá, os módulos podem ser usados individualmente (ver abaixo).

Todos os parâmetros (janela de observação, faixas de estrelas da busca, critério mínimo de inclusão, tentativas e backoff) ficam em [config.yaml](config.yaml).

### Seleção de repositórios e funil

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
truncar a consulta. Comparações de releases são paginadas e respostas 404 são
registradas sem interromper a coleta.

Saídas em `dados/`:

| Arquivo | Conteúdo |
|---|---|
| `metadados.csv` | um repositório por linha: `repositorio`, `url`, `estrelas`, `linguagem`, `default_branch`, `criado_em`, `idade_anos`, `contribuidores`, `workflows` |
| `funil.csv` | quantos repositórios restam em cada etapa, quantos saíram e os motivos agregados |
| `descartes.csv` | cada repositório descartado, com etapa e motivo |
| `releases.jsonl` | releases coletadas na janela e release principal anterior |
| `commits_entre_releases.jsonl` | commits paginados de cada comparação, com `commit.author.date` |
| `compare_404.jsonl` | releases cujo endpoint `compare` retornou 404 |
| `workflow_runs.jsonl` | runs do branch padrão e evento `push` |
| `coleta_resumo.json` | contagem de releases/runs válidos, 404 de compare e alertas mensais |

### Cache e retomada

Cada resposta da API é salva em `cache/` (um JSON por requisição, agrupado por repositório em `cache/repos/<dono>__<repo>/`). Se a coleta for interrompida (rate limit, queda de rede, `Ctrl+C`), basta rodar o mesmo comando de novo: o que já está no cache não é pedido outra vez. Respostas 404/409/422/451 também ficam no cache, porque não mudam se repetidas; respostas 5xx e 403 não.

Para forçar uma coleta nova, apague a pasta `cache/`.

### Rate limit e erros

- Quando `X-RateLimit-Remaining` chega a 0, o cliente espera até `X-RateLimit-Reset`. No rate limit secundário, respeita `Retry-After`; sem nenhum desses headers, consulta `GET /rate_limit` (que não consome cota).
- Respostas 5xx e erros de rede são repetidos com backoff exponencial (1, 2, 4, 8 s), até `http.max_tentativas` tentativas.

## Testes

```bash
pytest --cov=metricas --cov=pipeline --cov-report=term-missing
```

O CI ([.github/workflows/lab03-testes.yml](../.github/workflows/lab03-testes.yml)) roda os testes a cada push que altere esta pasta e falha se a cobertura de `metricas/` ficar abaixo de 80%.

## Estrutura

```text
Laboratorio03/
├── config.yaml          # janela, filtros, caminhos
├── requirements.txt
├── pipeline/
│   ├── http_client.py   # GET autenticado, paginação, cache, rate limit, backoff
│   ├── selecao.py       # busca fatiada, filtro de Actions, seleção da amostra
│   ├── metadados.py     # estrelas, linguagem, idade, contribuidores
│   └── funil.py         # funil.csv e descartes.csv
│   ├── releases.py      # releases e commits entre releases
│   ├── workflow_runs.py # runs segmentados por mês
│   └── coleta.py        # critério mínimo e persistência da coleta
├── metricas/            # funções puras de cálculo e classificação DORA
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
