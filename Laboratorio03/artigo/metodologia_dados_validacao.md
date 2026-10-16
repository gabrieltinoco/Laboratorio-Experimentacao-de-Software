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
| Tipo do projeto | 60 | [preencher] | [preencher] | [preencher] | [preencher] |
| Entregas reais | 60 | [preencher] | [preencher] | [preencher] | [preencher] |
| Release corretiva | 300 | [preencher] | [preencher] | [preencher] | [preencher] |

**Consenso.** Com dois avaliadores não existe maioria. Por isso, todos os itens divergentes foram discutidos em uma reunião de consenso, na qual os dois reabriram as evidências e registraram o rótulo final e a justificativa de cada decisão. Quando não houve acordo, aplicou-se uma regra conservadora definida no protocolo: `outro` para o tipo do projeto, `incerto` para entregas reais e `não` para release corretiva. Dos [preencher] itens divergentes, [preencher] precisaram dessa regra. Os rótulos de consenso servem de referência para a precisão, o recall e o F1 da heurística de release corretiva. O tipo do projeto de consenso é um dos fatores da RQ 06.

## Referências desta seção

- Cohen, J. (1960). A coefficient of agreement for nominal scales. *Educational and Psychological Measurement*, 20(1), 37–46.
- Fleiss, J. L. (1971). Measuring nominal scale agreement among many raters. *Psychological Bulletin*, 76(5), 378–382.
- Landis, J. R.; Koch, G. G. (1977). The measurement of observer agreement for categorical data. *Biometrics*, 33(1), 159–174.
