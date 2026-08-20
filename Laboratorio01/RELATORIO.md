# Relatório — Laboratório 01: Características de repositórios populares

**Versão 1 (entrega da Lab01S02).** Esta versão traz a introdução com as
hipóteses informais, a metodologia de coleta e a configuração do processo. Os
resultados numéricos consolidados e as visualizações das 7 RQs do enunciado, mais
as 2 propostas pelo grupo, são a entrega da Lab01S03; as seções de resultado
abaixo já registram o que a validação de consistência dos 1000 repositórios
revelou em cada parte.

- **Repositório:** https://github.com/gabrieltinoco/Laboratorio-Experimentacao-de-Software
- **GitHub Projects (v2):** https://github.com/users/gabrieltinoco/projects/2
- **Integrantes:** Arthur Miranda Pacher (`art1544`), Gabriel Lage Silva (`gabitolage`), Gabriel Lucas Tinoco de Aguiar (`gabrieltinoco`)

---

## 1. Introdução e hipóteses informais

O objeto de estudo são os 1.000 repositórios com maior número de estrelas no
GitHub. A pergunta de fundo é se "popular" implica um conjunto de características
de engenharia — maturidade, contribuição externa, cadência de release,
manutenção ativa, escolha de linguagem e disciplina no tratamento de issues.

A hipótese geral do grupo é que **estrela mede acervo, não atividade**: o
contador de estrelas é cumulativo e nunca decresce, então o top 1000 tende a
reunir tanto projetos vivos quanto projetos que foram muito populares no passado.
Se isso for verdade, cada RQ deve mostrar uma distribuição com cauda longa, e a
mediana — não a média — é o valor central a reportar.

Uma segunda hipótese, que atravessa várias RQs, é que o top 1000 **não é
composto só de software**. Listas "awesome", roteiros de estudo e coleções de
material didático são extremamente estreladas sem serem software distribuível, e
isso deve distorcer qualquer métrica que pressuponha um ciclo de
desenvolvimento (releases, pull requests, linguagem primária).

As hipóteses específicas por RQ, cada uma registrada na Issue do integrante
responsável:

| RQ | Métrica | Hipótese informal | Responsável / Issue |
|---|---|---|---|
| RQ01 | Idade do repositório | Repositórios populares tendem a ser maduros: esperamos que a maioria tenha pelo menos 5 anos, embora exista uma cauda de projetos novos. | `gabrieltinoco` — [#5](https://github.com/gabrieltinoco/Laboratorio-Experimentacao-de-Software/issues/5) |
| RQ02 | Total de pull requests aceitas | Repositórios populares tendem a receber muita contribuição externa: esperamos mediana alta de PRs aceitas e a maioria com pelo menos 500 PRs. | `gabrieltinoco` — [#6](https://github.com/gabrieltinoco/Laboratorio-Experimentacao-de-Software/issues/6) |
| RQ03 | Total de releases | Sistemas populares lançam releases com frequência | `art1544` — [#7](https://github.com/gabrieltinoco/Laboratorio-Experimentacao-de-Software/issues/7) |
| RQ04 | Tempo até a última atualização | Sistemas populares são atualizados com frequência | `art1544` — [#8](https://github.com/gabrieltinoco/Laboratorio-Experimentacao-de-Software/issues/8) |
| RQ05 | Linguagem primária | *a preencher* | `gabitolage` — [#9](https://github.com/gabrieltinoco/Laboratorio-Experimentacao-de-Software/issues/9) |
| RQ06 | Razão issues fechadas / total | *a preencher* | `gabitolage` — [#10](https://github.com/gabrieltinoco/Laboratorio-Experimentacao-de-Software/issues/10) |
| RQ07 | RQ02, RQ03 e RQ04 por linguagem | *a preencher* | `gabitolage` — [#11](https://github.com/gabrieltinoco/Laboratorio-Experimentacao-de-Software/issues/11) |
| RQ08 (proposta pelo grupo) | Licença SPDX | *a preencher* | `gabitolage` — [#13](https://github.com/gabrieltinoco/Laboratorio-Experimentacao-de-Software/issues/13) |
| RQ09 (proposta pelo grupo) | Cadência de releases (releases por ano de vida) | A cadência se mantém ao longo da vida do projeto | `art1544` — [#18](https://github.com/gabrieltinoco/Laboratorio-Experimentacao-de-Software/issues/18) |

As RQ08 e RQ09 não estão no enunciado: são questões propostas pelo próprio
grupo, uma por integrante que as levantou, a partir do que a coleta permitiu
perguntar além das 7 originais.

### RQ03 — Sistemas populares lançam releases com frequência?

**Hipótese.** Um projeto com dezenas de milhares de estrelas tende a ser
consumido como dependência por terceiros, e quem é consumido como dependência
precisa de versionamento publicado. Esperamos, portanto, mediana de releases alta
e pouquíssimos repositórios sem nenhuma release.

### RQ04 — Sistemas populares são atualizados com frequência?

**Hipótese.** A visibilidade gera um fluxo constante de issues e pull requests, e
esse fluxo mantém o repositório em movimento. Esperamos tempo curto desde a
última atualização para praticamente todos os repositórios.

### RQ09 (proposta pelo grupo) — A cadência de releases se mantém ao longo da vida do projeto?

**Métrica.** Cadência de releases = `total_releases / idade em anos`, cruzada com
a idade do repositório (RQ01) e com o tempo desde o último push (RQ04).

**Por que perguntar isso.** A RQ03 mede o **total absoluto** de releases, e essa
métrica tem um viés estrutural: um repositório de 15 anos teve três vezes mais
tempo para publicar releases que um de 5 anos. Parte do resultado da RQ03 pode
ser, então, idade disfarçada de cadência. Normalizar pela idade testa se a
resposta da RQ03 sobrevive, e amarra três RQs que hoje são respondidas
isoladamente: idade (RQ01), releases (RQ03) e atividade (RQ04).

**Hipótese.** Esperamos duas coisas. Primeira: que o total de releases cresça com
a idade, porque projeto mais velho teve mais tempo de publicar. Segunda: que a
cadência, uma vez normalizada, seja aproximadamente estável entre projetos novos
e antigos, porque a prática de versionar releases seria uma característica do
projeto, não da época em que ele nasceu.

---

## 2. Metodologia de coleta

### 2.1 Fonte e recorte

Os dados vêm da **API GraphQL v4 do GitHub**, consultada por script próprio do
grupo (`Laboratorio01/src/fetch_repos.py`). Não é usada nenhuma biblioteca de
terceiros que consulte a API do GitHub: a query é escrita à mão e enviada por
requisição HTTP direta.

O recorte é a busca `stars:>1 sort:stars-desc` no tipo `REPOSITORY`, tomando os
**1.000 primeiros resultados** — que é também o teto de resultados que o endpoint
`search` devolve para uma mesma query.

### 2.2 Paginação

A busca é paginada por cursor, usando `pageInfo.hasNextPage` e
`pageInfo.endCursor` do próprio `search`, com o cursor da página anterior sendo
passado no argumento `after` da requisição seguinte. O laço para quando 1.000
repositórios foram coletados ou quando a API sinaliza que não há próxima página.
Respostas com erro 5xx são repetidas com espera progressiva.

### 2.3 Campos coletados

Uma única query traz todos os campos necessários a todas as RQs, para não haver
risco
de o mesmo repositório ser lido em momentos diferentes:

| Campo GraphQL | Coluna no CSV | RQ |
|---|---|---|
| `nameWithOwner` | `repositorio` | identificação |
| `stargazerCount` | `estrelas` | recorte e RQ08 |
| `createdAt` | `created_at` | RQ01, RQ09 |
| `pullRequests(states: MERGED).totalCount` | `pull_requests_aceitas` | RQ02, RQ07 |
| `releases.totalCount` | `total_releases` | RQ03, RQ07, RQ09 |
| `updatedAt` | `ultima_atualizacao`, `dias_desde_ultima_atualizacao` | RQ04, RQ07 |
| `pushedAt` | `ultimo_push`, `dias_desde_ultimo_push` | RQ04, RQ07 |
| `primaryLanguage.name` | `linguagem_primaria` | RQ05, RQ07 |
| `issues.totalCount` | `issues_total` | RQ06 |
| `issues(states: CLOSED).totalCount` | `issues_fechadas`, `percentual_issues_fechadas` | RQ06 |
| `licenseInfo.spdxId` | `licenca` | RQ08 |

As colunas derivadas (`dias_desde_*`, `percentual_issues_fechadas`) são
calculadas no momento da coleta, a partir dos campos brutos, e os campos brutos
são preservados no CSV para permitir recálculo e auditoria.

Saída: `Laboratorio01/data/repositorios_top1000.csv`, uma linha por repositório.

### 2.4 Definição de "linguagens mais populares" (RQ05 e RQ07)

A referência adotada é o **GitHub Octoverse 2025**, e é a mesma em todo o
laboratório: TypeScript, Python, JavaScript, Java e C#. A lista está fixada em
`src/validate_sample.py` (constante `LINGUAGENS_POPULARES`), para que a RQ05 e a
RQ07 usem exatamente o mesmo conjunto.

### 2.5 Validação dos dados

Cada integrante valida a sua parte das RQs em script próprio, verificando
consistência estrutural campo a campo, distribuição, outliers e valores
ausentes nos 1.000 repositórios:

| Script | Cobertura |
|---|---|
| `src/rq01_rq02.py` | RQ01, RQ02 |
| `src/validate_sample_rq03_rq04.py` | RQ03, RQ04 |
| `src/validate_sample.py` | RQ05, RQ06, RQ07, RQ08 |
| `src/rq09_cadencia_releases.py` | RQ09 |

### 2.6 Limitações conhecidas da coleta

- **`releases.totalCount` satura em 1.000.** 21 repositórios do top 1000 marcam
  exatamente 1.000 releases; nesses casos o valor é um limite inferior, não a
  contagem real.
- **`updatedAt` não mede atividade de código.** O campo sobe a cada estrela ou
  watch recebido. Nesta população ele fica saturado (detalhado na RQ04).
- **A coleta não é atômica.** As 1.000 linhas são lidas ao longo de várias
  requisições, então um repositório que recebe push durante a coleta pode ficar
  com contagem de dias negativa por questão de minutos. Ocorreu em 1 caso.
- **`pullRequests(states: MERGED)` conta PR aceita de qualquer autor**, inclusive
  de mantenedores. É uma aproximação de "contribuição externa", não a medida
  exata.

---

## 3. Resultados por RQ

> Os valores consolidados e os gráficos das 7 RQs do enunciado e das 2 propostas
> pelo grupo são a entrega da Lab01S03. As
> seções abaixo registram o que a validação de consistência dos 1.000
> repositórios já mostrou.

### RQ01 — Idade do repositório

Não foram encontrados valores ausentes ou inválidos em `created_at` (0/1000). A idade mediana foi de **7,75 anos**, com média de 7,67, mínimo de 0,02 e máximo de 18,36 anos. Em relação à distribuição, 323 repositórios (32,3%) têm menos de 5 anos, 331 (33,1%) têm entre 5 e 10 anos e 346 (34,6%) têm 10 anos ou mais. Ao todo, 677 (67,7%) têm pelo menos 5 anos.

Pelo critério de Tukey, usando 1,5 x IQR, Q1 = 3,52 e Q3 = 11,36 anos, não foram identificados outliers. O resultado apoia a hipótese informal de maturidade para a maioria, mas a presença de 323 repositórios com menos de 5 anos impede tratá-la como universal.

### RQ02 — Total de pull requests aceitas

Não foram encontrados valores ausentes ou inválidos em `pull_requests_aceitas` (0/1000). A mediana foi de **768 PRs aceitas**, com média de 4.237,1, mínimo de 0 e máximo de 103.354. A distribuição foi: 20 repositórios (2,0%) com 0 PR, 396 (39,6%) entre 1 e 499, 398 (39,8%) entre 500 e 4.999 e 186 (18,6%) com 5.000 ou mais. Ao todo, 584 (58,4%) têm pelo menos 500 PRs aceitas.

A distribuição é fortemente assimétrica à direita: Q1 = 175, Q3 = 3416 e IQR = 3241. Pelo critério de Tukey, os valores acima de 8277 são outliers; foram identificados 124 (12,4%), incluindo `firstcontributions/first-contributions`, `llvm/llvm-project`, `elastic/elasticsearch`, `getsentry/sentry` e `home-assistant/core`. Esses valores não devem ser removidos, mas a mediana deve ser priorizada na interpretação. A mediana alta e 58,4% acima do corte apoiam a hipótese informal, enquanto a cauda extrema explica por que a média não é representativa.

### RQ03 — Total de releases

Nenhuma inconsistência estrutural em 1.000 repositórios e nenhum valor ausente.

| Estatística | Valor |
|---|---|
| Mediana | 39 releases |
| Média | 126,6 |
| Q1 / Q3 | 0 / 147 |
| Mínimo / máximo | 0 / 1.000 |

Distribuição:

| Faixa | Repositórios |
|---|---|
| Nenhuma release | 286 (28,6%) |
| 1 a 10 releases | 76 (7,6%) |
| Acima de 100 releases | 343 (34,3%) |

A distribuição é **bimodal**: um bloco de 28,6% sem release nenhuma e um bloco de
34,3% acima de 100. Como Q1 = 0, a média de 126,6 não descreve nada e a mediana
de 39 é o único valor central defensável.

Os 21 repositórios travados em 1.000 releases (entre eles
`langchain-ai/langchain`, `vercel/next.js`, `electron/electron`) precisam ser
lidos como ">= 1000" na análise da S03.

### RQ04 — Tempo até a última atualização

Nenhuma inconsistência estrutural e nenhum valor ausente nas quatro colunas
envolvidas.

**A métrica literal do enunciado não discrimina nesta população.** Usando
`updatedAt`: mediana 0 dia, Q1 = Q3 = 0, amplitude total de 0 a 2 dias, com 984
dos 1.000 repositórios (98,4%) em 0 dia e 100% na faixa "até 7 dias". A causa é
conhecida: o `updatedAt` sobe a cada estrela ou watch, e os repositórios mais
estrelados do GitHub recebem estrelas continuamente.

**Métrica efetiva: `pushedAt`**, que só sobe com push de código.

| Faixa desde o último push | Repositórios |
|---|---|
| Até 7 dias | 616 (61,6%) |
| 8 a 30 dias | 111 (11,1%) |
| 31 a 90 dias | 64 (6,4%) |
| 91 a 365 dias | 94 (9,4%) |
| Mais de 365 dias | **115 (11,5%)** |

Mediana 2 dias, Q1 = 0, Q3 = 49, máximo 2.451 dias. Os mais parados são
`exacity/deeplearningbook-chinese` (2.451 dias), `GitSquared/edex-ui` (1.764),
`lib-pku/libpku` (1.687), `adobe/brackets` (1.529) e
`floodsung/Deep-Learning-Papers-Reading-Roadmap` (1.361).

### RQ05 — Linguagem primária

*A preencher — [#9](https://github.com/gabrieltinoco/Laboratorio-Experimentacao-de-Software/issues/9), `gabitolage`.*

### RQ06 — Percentual de issues fechadas

*A preencher — [#10](https://github.com/gabrieltinoco/Laboratorio-Experimentacao-de-Software/issues/10), `gabitolage`.*

### RQ07 — RQ02, RQ03 e RQ04 por linguagem

*A preencher — [#11](https://github.com/gabrieltinoco/Laboratorio-Experimentacao-de-Software/issues/11), `gabitolage`.*

### RQ08 (proposta pelo grupo) — Licença e popularidade/contribuição

*A preencher — [#13](https://github.com/gabrieltinoco/Laboratorio-Experimentacao-de-Software/issues/13), `gabitolage`.*

### RQ09 (proposta pelo grupo) — Cadência de releases

Dos 1.000 repositórios, **714 (71,4%) têm cadência calculável**; os outros 286
não têm release nenhuma e, portanto, não têm cadência definida — o script trata
esse caso como ausência de versionamento, e não como cadência zero.

Cadência dos 714: mediana **14,88 releases/ano**, média 44,38, Q1 = 5,05,
Q3 = 38,88, mínimo 0,06, máximo 2.182.

**A idade não explica o total de releases.** Correlação de postos (Spearman,
calculada no próprio script, sem biblioteca externa):

| Par de variáveis | Correlação | n |
|---|---|---|
| Idade × total de releases | **+0,062** | 1.000 |
| Idade × cadência de releases | **−0,416** | 714 |

O limite de ruído para essa amostra é ±0,073, então o +0,062 é indistinguível de
zero: **repositório mais velho não tem mais releases**. Já o −0,416 é muito acima
do limite, e no sentido oposto ao esperado: **a cadência cai conforme o projeto
envelhece.**

O resultado sobrevive aos dois testes de robustez: excluindo os repositórios com
menos de 1 ano de vida, onde dividir por uma fração de ano infla a cadência, a
correlação vai a −0,348 (n = 656); excluindo também os 21 que estão no teto de
1.000 releases da API, vai a −0,353 (n = 635). Sinal e ordem de grandeza se
mantêm.

**Cadência por faixa de idade** — o resultado central da RQ09:

| Faixa de idade | n | Mediana de releases | Mediana de cadência |
|---|---|---|---|
| Até 3 anos | 136 | 40 | **43,85 rel/ano** |
| 3 a 7 anos | 188 | 108 | 23,92 rel/ano |
| 7 a 12 anos | 242 | 116 | 12,25 rel/ano |
| Mais de 12 anos | 149 | 98 | **6,76 rel/ano** |

O total de releases quase não varia entre as faixas (40, 108, 116, 98), mas a
cadência cai monotonicamente, por um fator de mais de 6 entre a faixa mais nova e
a mais velha.

**Cadência por grupo de atividade** (cruzamento com a RQ04):

| Grupo | n | Mediana de cadência | Idade mediana |
|---|---|---|---|
| Ativo (push ≤ 30 dias) | 591 | 18,19 rel/ano | 7,3 anos |
| Morno (31 a 365 dias) | 80 | 6,47 rel/ano | 9,0 anos |
| Parado (> 365 dias) | 43 | 4,05 rel/ano | 9,3 anos |

**Os 286 sem release.** Idade mediana de 8,2 anos, mediana de 42 dias sem push, e
**56,3% recebeu push nos últimos 90 dias**. Não são projetos mortos: são
repositórios mantidos que simplesmente não versionam releases — listas, roteiros
de estudo e coleções de material.

**Extremos.** No topo, `stablyai/orca` (2.182 rel/ano — 932 releases em 5 meses),
`ruvnet/ruflo` (822), `openai/codex` (736): todos projetos recentes, quase todos
de ferramental de IA. Na base, `moment/moment` (0,06 — uma release em 15,5 anos),
`DefinitelyTyped/DefinitelyTyped` (0,07) e `discourse/discourse` (0,07).

---

## 4. Discussão: hipótese vs. resultado

### RQ03 — parcialmente confirmada

Entre os repositórios que de fato são software distribuível, a hipótese se
sustenta com folga: 34,3% do top 1000 passa de 100 releases. Mas quase um terço
(28,6%) não publica release nenhuma, o que confirma a segunda hipótese geral do
grupo: "repositório popular no GitHub" e "software distribuível" não são a mesma
coisa. A conclusão de método é que a RQ03 deve ser reportada separando os dois
grupos, e não em um único número agregado.

### RQ04 — confirmada para a maioria, com uma correção de método

A hipótese se confirma para a maior parte da população: 61,6% recebeu push na
última semana. Mas 11,5% está sem push há mais de um ano, o que sustenta a
hipótese geral de que estrela é métrica de acervo. O caso mais eloquente é o
`adobe/brackets`, um editor oficialmente descontinuado que segue no top 1000 por
estrelas acumuladas.

A correção de método é que a métrica literal da RQ04 (`updatedAt`) tem de ser
substituída pelo `pushedAt` na análise da S03: reportar a mediana de 0 dia do
`updatedAt` como resposta da RQ04 seria reportar um artefato da API, e não uma
característica dos sistemas estudados.

### RQ09 — as duas hipóteses refutadas, e uma métrica da RQ03 posta em dúvida

As duas partes da hipótese caíram.

A primeira parte — "o total de releases cresce com a idade" — foi refutada: a
correlação entre idade e total de releases é +0,062, indistinguível de zero para
essa amostra. Isso é, em si, um alívio metodológico: significa que o resultado da
RQ03 **não** é um artefato de repositórios velhos terem acumulado mais tempo.

A segunda parte — "a cadência é estável entre gerações" — foi refutada com força e
no sentido contrário: a cadência cai de 43,85 releases/ano nos projetos de até 3
anos para 6,76 nos de mais de 12, um fator de mais de 6, com correlação de −0,416
que resiste a dois cortes de robustez.

A explicação que os extremos sugerem é que **não estamos medindo cadência de
equipe, estamos medindo cadência de ferramenta**. Os projetos no topo
(`stablyai/orca`, `openai/codex`, `ruvnet/ruflo`) publicam release a cada merge,
por pipeline automatizado de integração contínua. Os da base (`moment/moment`,
`discourse/discourse`) são de uma época em que release era um evento manual, com
changelog escrito à mão. Ou seja: o que a RQ03 lê como "volume de releases" é, em
boa parte, **a prática de release da geração em que o projeto nasceu**.

A consequência prática para o laboratório é direta: **comparar o total de
releases de um projeto de 2013 com um de 2025 compara duas culturas de
engenharia, não dois níveis de atividade.** Na análise da S03, a RQ03 deve ser
reportada com a cadência ao lado do total, e qualquer comparação entre
repositórios de idades muito diferentes precisa dessa ressalva.

O cruzamento com a RQ04 acrescenta uma leitura no sentido inverso, e essa
confirmatória: quem está parado tem cadência histórica baixa (4,05 rel/ano contra
18,19 dos ativos). Cadência baixa e abandono andam juntos — o que sugere que a
cadência funciona como indicador de saúde do projeto, algo que nem a RQ03 nem a
RQ04 medem isoladamente.

### Demais RQs

*A preencher pelos responsáveis, conforme a tabela da seção 1.*

---

## 5. Configuração do processo

O fluxo de trabalho no GitHub Projects (v2), com o critério de entrada e saída de
cada coluna, o limite de WIP e sua justificativa, e a rotina de snapshot, está
documentado em [`PROCESSO.md`](PROCESSO.md). Em resumo:

- **Colunas (campo Status):** `Backlog → To do → Doing → Review → Done`.
- **Limite de WIP em Doing:** 2 cartões por integrante, 6 no board com o trio
  completo. O número acompanha a divisão de duas RQs por integrante por sprint e
  a janela semanal de trabalho, e segue a sugestão das regras da disciplina.
- **Cartões = Issues** do repositório, sempre com Assignee. Não há draft issues.
- **Commits** referenciam o número da Issue correspondente.
- **Snapshots:** exportados por `src/export_project_snapshot.py` no fechamento de
  cada sprint e acumulados em `data/project_snapshots.csv`.

O print do board com o fluxo completo do Lab01 é anexado na entrega do relatório
final, conforme o enunciado.
