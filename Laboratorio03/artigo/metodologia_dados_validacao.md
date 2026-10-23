# Metodologia: fonte de dados, seleção e validação manual

Esta parte da Metodologia cobre a fonte de dados, a janela de observação, o funil de seleção e o protocolo da validação manual. As definições operacionais das métricas, suas variantes e as versões da heurística de release corretiva são descritas em uma seção à parte.

## Fonte de dados

Os dados vêm da API REST pública do GitHub (`api.github.com`), consultada por um cliente HTTP escrito pelo grupo, sem bibliotecas de acesso à API. O cliente segue a paginação pelo cabeçalho `Link`, salva cada resposta em disco e espera automaticamente quando a cota de requisições acaba (cabeçalhos `X-RateLimit-Remaining` e `X-RateLimit-Reset`). Erros temporários (5xx) são repetidos com *backoff* exponencial. Por causa do cache, uma coleta interrompida continua de onde parou, e o dataset final pode ser regenerado sem novas chamadas à API.

Para cada repositório foram usados os seguintes endpoints: `/search/repositories` (candidatos e metadados), `/actions/workflows` (uso de GitHub Actions), `/contributors` (número de contribuidores), `/releases` (deploys), `/compare/{base}...{head}` (commits entre duas releases consecutivas, com paginação) e `/actions/runs` (execuções de CI). A coleta foi feita em outubro de 2026.

## Janela de observação

A janela vai de 1º de outubro de 2025 a 30 de setembro de 2026 (365 dias, ≈ 52,1 semanas). Só entram no cálculo as releases publicadas e os workflow runs criados nesse intervalo. A exceção é a release imediatamente anterior ao início da janela, coletada apenas para delimitar os commits da primeira release da janela no cálculo do lead time. Métricas que dependem de datas absolutas, como a idade do repositório, usam o fim da janela como referência, para não variarem com o dia da coleta.

## Seleção dos repositórios

A busca do GitHub devolve no máximo 1.000 resultados por consulta. Por isso, a busca por repositórios com pelo menos 1.000 estrelas, não arquivados e com *push* desde o início da janela foi dividida em oito faixas de estrelas (1.000–1.500, 1.501–2.000, 2.001–3.000, 3.001–5.000, 5.001–10.000, 10.001–20.000, 20.001–50.000 e acima de 50.000). Repositórios que apareceram em mais de uma faixa foram contados uma só vez. Mesmo fatiada, a busca não alcança todos os repositórios das faixas mais baixas, que têm milhares de resultados. Dentro de cada faixa, ela devolve os de mais estrelas.

Para que a amostra não fique concentrada nos repositórios mais populares, os candidatos foram embaralhados com semente fixa (42) e avaliados nessa ordem até a amostra atingir 306 repositórios, acima do mínimo de 300 exigido. Cada candidato passou por três filtros, nesta ordem:

1. **Uso de GitHub Actions:** repositórios sem workflows (`total_count = 0`) foram descartados antes de qualquer outra chamada.
2. **Metadados:** repositórios cujos metadados não puderam ser obtidos (erros 4xx) foram descartados.
3. **Critério mínimo de inclusão:** pelo menos 5 releases publicadas (`draft = false`, `prerelease = false`) e 50 workflow runs válidos (conclusão de sucesso ou falha) no *default branch*, disparados por `push`, dentro da janela.

Os workflow runs foram consultados mês a mês, porque a API também limita cada consulta filtrada a 1.000 resultados. Os meses que atingiram esse teto foram registrados (coluna `meses_no_teto_de_runs`). O funil de seleção está na Tabela X.

**Tabela X.** Funil de seleção dos repositórios.

| Etapa | Repositórios | Descartados | Principais motivos |
|---|---:|---:|---|
| Encontrados na busca | 37.401 | — | soma do `total_count` das oito faixas |
| Candidatos acessíveis | 7.451 | 29.950 | teto de 1.000 resultados por consulta |
| Candidatos avaliados | 1.128 | 6.323 | não avaliados: a amostra foi completada antes |
| Com GitHub Actions | 964 | 164 | sem workflows |
| Metadados coletados | 964 | 0 | — |
| ≥ 5 releases e ≥ 50 runs válidos | **306** | 658 | menos de 5 releases e menos de 50 runs (391); só menos de 5 releases (179); só menos de 50 runs (88) |

Dos 964 candidatos com GitHub Actions, só 32% atenderam ao critério mínimo de inclusão. O motivo mais comum de descarte foi a falta de releases publicadas: 570 dos 658 repositórios descartados nessa etapa tinham menos de 5 releases na janela, o que sugere que muitos projetos populares não usam as releases do GitHub como mecanismo de entrega. Em 35 dos 306 repositórios, ao menos um mês atingiu o teto de 1.000 workflow runs por consulta, e as métricas de CI desses meses podem estar subestimadas. Seis releases ficaram fora do cálculo de lead time porque a comparação com a release anterior estava indisponível (tag apagada ou diff grande demais para a API).

O dataset final (`dados/repositorios.csv`) tem uma linha por repositório, com os metadados, as métricas em todas as variantes e a classificação DORA. Cada coluna está documentada em `dados/DICIONARIO.md`, com tipo, unidade e fórmula ou origem na API.

## Validação manual

As métricas são calculadas a partir de *proxies* (release como deploy, release corretiva como sinal de falha). Para medir o quanto esses critérios automáticos concordam com o julgamento humano, o grupo construiu uma amostra-ouro.

**Sorteio.** Foram sorteados 60 dos 306 repositórios (`DataFrame.sample(n=60, random_state=42)`) e, em cada um, 5 releases publicadas na janela, com a mesma semente, num total de 300 releases. O sorteio e os parâmetros estão no repositório do grupo, então ele pode ser refeito.

**Rotulação.** Cada avaliador recebeu uma planilha gerada automaticamente, com links para o repositório, para a página de cada release e para a lista de commits desde a release anterior. A planilha não mostrava a saída da heurística. Os avaliadores rotularam de forma independente, sem consultar um ao outro, três dimensões: (i) o tipo do projeto (biblioteca/framework, aplicação/serviço, ferramenta CLI ou outro); (ii) se as releases representam entregas reais ao usuário (sim, não ou incerto); e (iii) se cada uma das 5 releases é corretiva (sim ou não), isto é, se o objetivo principal dela é corrigir um defeito recente. Os critérios de cada rótulo foram fixados antes da rotulação em um protocolo escrito (`validacao/PROTOCOLO.md`). Ele exige, por exemplo, que a release corretiva seja julgada pelo conteúdo das notas e dos commits, e não pelo número da versão, que é justamente o sinal usado pela heurística.

**Concordância.** O enunciado prevê três avaliadores e o kappa de Fleiss. Como o grupo tem dois integrantes, a medida principal de concordância é o kappa de Cohen [Cohen 1960], que é a medida usual para dois avaliadores. Para comparação com os demais grupos, o kappa de Fleiss também é reportado. Os dois corrigem a concordância esperada por acaso e foram interpretados pela escala de Landis e Koch [1977]. A Tabela Y resume a concordância da rotulação independente, antes do consenso.

**Tabela Y.** Concordância entre os dois avaliadores (n = itens rotulados).

| Dimensão | n | Concordância observada | κ de Cohen | κ de Fleiss | Interpretação |
|---|---:|---:|---:|---:|---|
| Tipo do projeto | 60 | 0,7833 | 0,6923 | 0,6908 | substancial |
| Entregas reais | 60 | 0,8500 | 0,4105 | 0,3832 | moderada |
| Release corretiva | 300 | 0,9300 | 0,8496 | 0,8496 | quase perfeita |

**Consenso.** Com dois avaliadores não existe maioria, então todos os 43 itens
divergentes foram decididos individualmente: 13 de tipo do projeto, 9 de
entregas reais e 21 de release corretiva. As decisões foram redigidas com o
apoio de um assistente de IA (Claude), a pedido da dupla. O assistente reabriu
as evidências de cada item (README do repositório, notas da release, commits
do `compare` e arquivos publicados nas releases) e aplicou os critérios do
protocolo. O rótulo e uma justificativa de uma frase estão em
`validacao/divergencias.csv`. A Tabela Y2 resume as decisões.

**Tabela Y2.** Decisões de consenso nos itens divergentes.

| Dimensão | Divergências | Decisão |
|---|---:|---|
| Tipo do projeto | 13 | 8 aplicação/serviço, 3 ferramenta CLI, 1 biblioteca/framework, 1 outro |
| Entregas reais | 9 | 9 sim |
| Release corretiva | 21 | 7 sim, 14 não |

Três padrões explicam a maior parte das divergências. Em tipo do projeto, o
caso mais frequente foi o *firmware* (ESPectre, DS5Dongle, PebbleOS), que um
avaliador tratou como aplicação e o outro como `outro`. O consenso adotou
aplicação/serviço, porque o firmware é executado pelo usuário final. Em
entregas reais, todas as divergências opunham `sim` a `incerto`. Em todos os
casos as releases distribuem pacotes (npm, PyPI, Maven Central) ou binários
por plataforma, e o rótulo ficou `sim`. Em release corretiva, as divergências
vieram de releases mistas e de releases com notas vazias. A regra 3 do
protocolo (`sim` só quando as correções são maioria clara e não há
funcionalidade destacada) resolveu as mistas. Nas releases com notas vazias ou
sem conteúdo próprio, a decisão seguiu os commits, e `não` foi usado quando
eles não mostravam correção clara (2 casos). Nenhum item ficou sem acordo, então a regra
conservadora não precisou ser aplicada.

Com o consenso, a amostra-ouro tem 107 releases corretivas entre 300 (35,7%).
Os tipos ficaram assim: 25 aplicação/serviço, 21 biblioteca/framework, 11
ferramenta CLI e 3 outro. Em entregas reais, 56 repositórios ficaram com `sim`
e 4 com `incerto` (rótulo dado pelos dois avaliadores). Nenhum ficou com `não`.

## Definições operacionais, variantes e heurística

Na definição de referência, cada release publicada que não seja draft nem
pré-release representa um deploy. A frequência é o número dessas releases
dividido pelo número de semanas da janela. Para a análise de sensibilidade da
RQ 07, também são calculadas a frequência incluindo pré-releases publicadas e
a frequência de tags, usando como data da tag o `commit.author.date` do commit
apontado (coletado via GraphQL, seguindo tags anotadas até o commit). O lead
time é calculado por release (mediana da publicação menos o commit mais antigo
do compare) e por commit (mediana da publicação menos a data de cada commit).
Essas variantes não são intercambiáveis: uma alteração antiga incluída em uma
release afeta a medida por release mais do que a mediana por commit.

| Combinação | Frequência de deploy | Lead time | CFR |
|---|---|---|---|
| C1 (referência) | Releases principais | Por release (a) | Por CI (a) |
| C2 | Releases principais e pré-releases | Por commit (b) | Por releases (b) |
| C3 | Tags, datadas pelo commit apontado | Por commit (b) | Por CI (a) |

O tempo de recuperação é mantido constante nas três combinações. C2 e C3
seguem as combinações de sensibilidade definidas no enunciado.

O CFR (a) usa falhas sobre runs válidos de CI. O CFR (b) usa como denominador
as releases principais fora dos últimos sete dias da janela; uma release do
denominador é considerada falha quando alguma release corretiva é publicada
nos sete dias seguintes. Releases dos últimos sete dias são censuradas e
excluídas do denominador. A versão inicial da heurística (v1) marca uma release
como corretiva se (i) o SemVer válido muda somente o patch para um número
superior ou (ii) as mensagens dos commits entre as releases contêm `fix`,
`hotfix`, `revert` ou `bugfix`, sem distinção de maiúsculas e minúsculas.

A avaliação compara as previsões apenas com `consenso_releases.csv` e calcula
precisão, recall e F1. Cada resultado é gravado sem sobrescrever versões
anteriores em `validacao/avaliacao_heuristica.csv`.

A v1 acertou quase todas as corretivas (recall 0,94), mas com precisão de
0,38. Releases com muitos commits quase sempre têm algum `fix`, e a v1 marca
como corretivas releases que trazem funcionalidades novas. Para revisar a
heurística sem ajustá-la aos mesmos itens usados para medi-la, os 60
repositórios da amostra-ouro foram divididos em duas metades de 30, com a
mesma semente do sorteio (`--particao` em `validacao.avaliar_heuristica`). As
regras candidatas foram comparadas só na metade de desenvolvimento. A melhor
delas foi fixada antes de a metade de teste ser avaliada, e a metade de teste
foi usada uma única vez. Os rótulos de referência não foram alterados.

A v2 segue o critério do protocolo e julga primeiro pelas notas da release.
Ela marca a release como corretiva quando (i) as notas são dominadas por
correções, isto é, têm uma seção de correções (*Bug Fixes*, *Fixed*,
*Patch Changes*) sem seção de funcionalidades, ou têm mais itens de correção do
que de funcionalidade. Também marca quando (ii) as notas não destacam
funcionalidade nova, o SemVer muda apenas o patch e os títulos dos commits têm
pelo menos tantas correções quanto funcionalidades (`feat:`, *add*,
*implement*, *new*…). Diferente da v1, um commit `fix` isolado em uma release
*minor* não basta para marcá-la.

**Tabela Z.** Desempenho das versões da heurística contra o consenso.

| Versão | Regra | Conjunto | n | Precisão | Recall | F1 |
|---|---|---|---:|---:|---:|---:|
| v1 | patch isolado ou commit com termo corretivo | todos | 300 | 0,375 | 0,944 | 0,537 |
| v1 | | teste | 150 | 0,290 | 0,950 | 0,444 |
| v2 | notas dominadas por correções, ou patch sem funcionalidade e commits de correção ≥ funcionalidade | desenvolvimento | 150 | 0,624 | 0,791 | 0,697 |
| v2 | | **teste** | **150** | **0,500** | **0,725** | **0,592** |
| v2 | | todos | 300 | 0,573 | 0,766 | 0,656 |

A estimativa honesta do desempenho da v2 é a da metade de teste, F1 de 0,59.
O valor sobre as 300 releases inclui os itens usados para escolher a regra e
é otimista. A v2 dobra a precisão da v1 e mantém recall acima de 0,7, mas
**não alcança a meta planejada de F1 ≥ 0,70**. Ela é a versão usada no
dataset final (`cfr_releases`, `releases_corretivas` e `rework_rate`).

Nas 300 releases, a v2 erra 61 falsos positivos e 25 falsos negativos. Em 59
dos 61 falsos positivos as notas existem. A maioria são releases mistas: têm
funcionalidades destacadas, mas mais itens de correção do que de
funcionalidade (ex.: openapi-generator, bruno, nuclei), e o protocolo as
rotula como `não`. Os demais são patches de manutenção, com atualização de
dependências e refatorações (ex.: AssetRipper, Sway). Os falsos negativos são,
na maior parte, releases que descrevem a correção em prosa, sem seção nem
itens (“This release fixes…”, “This is a security release”, como em Rhino e
Anki), ou releases que não são patch e cujas notas só têm instruções de
download. Uma versão futura poderia tratar a presença de seção de
funcionalidades como impeditiva, independentemente da contagem de itens, e
reconhecer frases corretivas em prosa. Essa versão precisaria de uma nova
amostra de teste, porque a metade de teste atual já foi usada. Por isso, o
CFR (b) e o rework rate continuam sendo *proxies* com erro conhecido, e as
conclusões que dependem deles são tratadas com cautela nos resultados.

## Referências desta seção

- Cohen, J. (1960). A coefficient of agreement for nominal scales. *Educational and Psychological Measurement*, 20(1), 37–46.
- Fleiss, J. L. (1971). Measuring nominal scale agreement among many raters. *Psychological Bulletin*, 76(5), 378–382.
- Landis, J. R.; Koch, G. G. (1977). The measurement of observer agreement for categorical data. *Biometrics*, 33(1), 159–174.
