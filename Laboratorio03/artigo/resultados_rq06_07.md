# Resultados e Discussão: RQ 06 e RQ 07

As análises foram executadas sobre `dados/repositorios.csv` (306
repositórios). Os scripts são reexecutáveis com
`python -m analise.rq06_rq07`. As tabelas completas, incluindo as estatísticas
por subgrupo, os tamanhos de efeito pareados e as classificações individuais,
estão em `analise/saidas/`.

## RQ 06 — Características associadas ao desempenho

Foram comparadas seis métricas (frequência de deploy, lead time por release,
lead time por commit, CFR por CI, CFR por releases e recuperação) em três
fatores disponíveis no dataset: linguagem principal, quartil de estrelas e
quartil de idade. Os quartis foram formados por postos, para manter quatro
grupos de tamanhos semelhantes. Sem rótulos de consenso, o tipo de projeto não
pôde ser analisado; essa dimensão depende da conclusão da validação manual.

Para cada uma das 18 combinações fator-métrica, foi aplicado Kruskal-Wallis.
Os 18 p-valores foram corrigidos juntos pelo método de Holm. ε² é reportado
como H/(n−1), conforme definido no planejamento. Cliff's δ e a interpretação
de magnitude de Romano estão calculados para todos os pares de grupos nos
arquivos de saída; os valores são tamanhos de efeito descritivos, não testes
post-hoc.

**Tabela RQ06.** Combinações com p < 0,05 após correção de Holm.

| Fator | Métrica | n | H | p ajustado (Holm) | ε² |
|---|---|---:|---:|---:|---:|
| Linguagem | Frequência | 298 | 39,44 | 0,0055 | 0,133 |
| Linguagem | Lead time por release | 298 | 51,94 | < 0,001 | 0,175 |
| Linguagem | CFR por releases | 297 | 40,06 | 0,0049 | 0,135 |
| Quartil de estrelas | Lead time por commit | 306 | 18,46 | 0,0042 | 0,061 |
| Quartil de idade | Frequência | 306 | 23,85 | < 0,001 | 0,078 |
| Quartil de idade | Lead time por release | 306 | 67,35 | < 0,001 | 0,221 |
| Quartil de idade | Lead time por commit | 306 | 68,81 | < 0,001 | 0,226 |
| Quartil de idade | CFR por releases | 305 | 51,06 | < 0,001 | 0,168 |
| Quartil de idade | Recuperação | 284 | 22,60 | < 0,001 | 0,080 |

Os padrões por idade não são monotônicos em todas as métricas. A mediana da
frequência cai de 0,537 releases/semana no quartil mais jovem para 0,288 no
mais antigo; os medianos de lead time crescem do Q1 até o Q3 e recuam no Q4.
O CFR por releases é mais alto no Q1 (0,691) do que nos demais quartis
(0,250–0,300). A associação estatística entre idade e desempenho não deve ser
interpretada como efeito causal: idade, tamanho, maturidade e práticas de
releases podem estar confundidos.

Para estrelas, somente o lead time por commit permaneceu associado após
Holm; suas medianas foram 9,07, 8,49, 15,65 e 21,04 dias do Q1 ao Q4. Embora
compatível com maior atraso em parte dos repositórios mais populares, não
houve evidência corrigida de diferença na frequência. Linguagem apresentou
diferenças globais em frequência, lead time por release e CFR por releases.
O teste global não indica quais linguagens diferem entre si, e há grupos
pequenos; os pares e Cliff's δ devem ser lidos como descrição, não como
confirmação de comparações individuais.

## RQ 07 — Sensibilidade às definições operacionais

C1 é a referência (releases principais, lead time por release e CFR por CI).
C2 troca a frequência para incluir pré-releases publicadas; C3 usa a
frequência de tags, datadas pelo commit apontado. Lead time, CFR e recuperação
permanecem iguais nas três combinações. As categorias gerais só são
comparadas nos 284 repositórios com as quatro métricas classificáveis.

**Tabela RQ07.** Mudança da categoria geral e kappa ponderado linear.

| Par | n | Mudaram de categoria | % que mudou | κ ponderado |
|---|---:|---:|---:|---:|
| C1 × C2 | 284 | 8 | 2,8% | 0,962 |
| C1 × C3 | 284 | 22 | 7,7% | 0,895 |
| C2 × C3 | 284 | 14 | 4,9% | 0,932 |

Na categoria de frequência, 25/306 repositórios mudaram entre C1 e C2
(8,2%), 58/306 entre C1 e C3 (19,0%) e 33/306 entre C2 e C3 (10,8%). Como as
demais métricas ficam fixas, essas alterações são também a origem das mudanças
na categoria geral. A substituição por tags provocou mais mudanças que a
inclusão de pré-releases, contrariando a expectativa registrada antes da
análise; ainda assim, as três combinações mantiveram concordância geral alta
(κ ponderado de 0,895 a 0,962).

## Limitações

O tipo do projeto, fator previsto para a RQ06, permanece pendente porque
`consenso_repositorios.csv` ainda não foi produzido. Os resultados cobrem
características observáveis do CSV, mas não substituem essa análise quando o
consenso estiver pronto. Além disso, os testes não controlam confundidores,
os quartis refletem esta amostra específica e grupos raros de linguagem têm
poucas observações. A correção de Holm reduz falsos positivos nas 18
comparações globais, mas não transforma associações em relações causais.
