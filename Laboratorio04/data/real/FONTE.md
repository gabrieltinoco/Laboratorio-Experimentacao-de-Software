# Fonte dos dados reais: `prs.csv`

## Resumo

| Item | Valor |
|---|---|
| Repositório | [microsoft/PowerToys](https://github.com/microsoft/PowerToys) |
| Bot de revisão | `copilot-pull-request-reviewer[bot]` (GitHub Copilot code review) |
| Período | PRs com **merge** entre 01/08/2026 e 31/10/2026 |
| Data da coleta | 04/11/2026 |
| Observações | **30 PRs com bot** e **30 PRs sem bot** (60 no total) |
| Script | [`src/coleta.py`](../../src/coleta.py) (`python -m src.coleta`) |

## Por que este repositório

- **Volume:** 497 PRs com merge no período, o suficiente para sortear 30 por grupo sem esgotar nenhum dos dois.
- **Os dois grupos convivem no mesmo período:** no PowerToys, a revisão do Copilot é pedida PR a PR (não é automática para todos). Cerca de 1 em cada 5 PRs com merge no período recebeu review do bot. Repositórios como `microsoft/vscode` e `microsoft/TypeScript` foram descartados porque o bot revisa praticamente todos os PRs, e então não sobra grupo "sem bot".
- **PRs abertos por pessoas e revisados por pessoas:** é um projeto grande, com equipe da Microsoft e contribuidores externos, em que o merge depende de aprovação humana.

## Critério dos grupos

- **`com_bot`:** o PR tem pelo menos uma review de `copilot-pull-request-reviewer[bot]` em `GET /repos/microsoft/PowerToys/pulls/{n}/reviews`.
- **`sem_bot`:** o PR não tem nenhuma review desse bot.
- **Excluídos:** PRs cujo autor é um bot (`user.type == "Bot"`, login terminado em `[bot]` ou o agente `Copilot`), porque o merge deles segue um fluxo automático. Dos 497 PRs, 14 foram excluídos por isso, e restaram 483.
- Outros bots de serviço (CI, verificação de licença/CLA) comentam em PRs dos dois grupos e **não** contam como "bot de revisão".

## Como a amostra foi sorteada

1. A API de busca lista os PRs com `is:pr is:merged merged:2026-08-01..2026-10-31`.
2. Os 483 PRs abertos por pessoas são ordenados por número e embaralhados com `numpy.random.default_rng(42)`.
3. Nessa ordem, cada PR é classificado pelas suas reviews. Os primeiros 30 de cada grupo entram na amostra, e foi preciso avaliar 132 PRs para fechar os dois grupos.
4. Para os 60 PRs sorteados, `GET /pulls/{n}` traz `created_at`, `merged_at` e o tamanho do PR.

## Colunas de `prs.csv`

| Coluna | Descrição |
|---|---|
| `numero` | número do PR |
| `grupo` | `com_bot` ou `sem_bot` |
| `created_at` | abertura do PR (UTC, ISO 8601) |
| `merged_at` | merge do PR (UTC, ISO 8601) |
| `horas_ate_merge` | `merged_at − created_at`, em horas |
| `url` | link do PR |
| `autor` | login de quem abriu o PR |
| `arquivos_alterados` | arquivos alterados (só para a discussão de limitações) |
| `linhas_alteradas` | linhas adicionadas + removidas (só para a discussão de limitações) |

## Como refazer a coleta

```bash
cd Laboratorio04
export GITHUB_TOKEN=ghp_...       # Windows PowerShell: $env:GITHUB_TOKEN = "ghp_..."
python -m src.coleta
```

O token precisa só de leitura de repositórios públicos e é lido apenas da variável de ambiente. As respostas da API ficam em `cache/` (fora do git). Rodar de novo com o cache gera o mesmo CSV sem chamar a API. Uma coleta do zero faz cerca de 200 requisições.

> Reviews podem ser apagadas e PRs podem ser editados depois da coleta. Uma coleta nova, sem o cache, pode dar um resultado um pouco diferente. O CSV commitado é a referência do laboratório.

## Visão rápida dos dados

| Grupo | n | Mediana (h) | Média (h) | Mín (h) | Máx (h) | Linhas alteradas (mediana) |
|---|---|---|---|---|---|---|
| com_bot | 30 | 37,1 | 235,9 | 0,9 | 2.842 | 126 |
| sem_bot | 30 | 51,8 | 332,2 | 0,02 | 4.419 | 559 |

- **Muito assimétrico:** nos dois grupos a média fica de 5 a 6 vezes acima da mediana, com coeficiente de assimetria de 3,9 (com bot) e 4,4 (sem bot). Poucos PRs que ficaram abertos por semanas ou meses puxam a média para cima.
- **Em escala log, quase normal:** a assimetria de `log(horas)` cai para −0,06 (com bot) e −1,12 (sem bot), o que justifica a lognormal (ver `src/parametros.py`).
- **Outliers:** o PR [#45846](https://github.com/microsoft/PowerToys/pull/45846) (sem bot) levou 4.419 h (~6 meses) até o merge. Já o PR [#49984](https://github.com/microsoft/PowerToys/pull/49984) (sem bot) teve merge em 1 minuto apesar de alterar 5.088 linhas, provavelmente uma integração de branch. Os dois foram mantidos porque são dados reais do processo.

## Limitações

- **Estudo observacional:** o bot não foi atribuído aos PRs por sorteio. Quem pede a revisão do Copilot escolhe em quais PRs fazer isso, então os grupos podem diferir em outras coisas além do bot.
- **Os grupos diferem em tamanho:** na amostra, os PRs com bot são bem menores (mediana de 126 linhas × 559 sem bot). PRs menores tendem a ser revisados mais rápido, então uma diferença no tempo até o merge não pode ser atribuída só ao bot.
- **Autores repetidos:** 25 autores distintos, 6 deles nos dois grupos,, e o mais frequente aparece 8 vezes. As observações não são totalmente independentes, porque cada pessoa tem seu próprio ritmo.
- **Recorte pelo merge:** só entram PRs que **já tiveram merge** no período. PRs abertos ainda sem merge e PRs fechados sem merge ficam de fora. Por isso, PRs que demoram muito estão sub-representados (alguns dos sorteados foram abertos em fevereiro de 2026).
- **Um único repositório e um único bot:** o resultado não se generaliza para outros projetos nem para outros bots de revisão.
