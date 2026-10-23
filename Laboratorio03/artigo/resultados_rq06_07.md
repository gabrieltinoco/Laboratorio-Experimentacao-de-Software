# Resultados e Discussão: RQ 06 e RQ 07

As análises foram executadas sobre `dados/repositorios.csv` (306
repositórios). O script `python -m analise.rq06_rq07` gera as tabelas
detalhadas em `analise/saidas/`.

## RQ 06 — Características associadas ao desempenho

Foram comparadas seis métricas (frequência de deploy, lead time por release,
lead time por commit, CFR por CI, CFR por releases e recuperação) em quatro
fatores: linguagem principal, quartis de estrelas, quartis de idade e tipo do
projeto. Os quartis foram formados por postos, para manter quatro grupos de
tamanhos semelhantes. O tipo do projeto vem dos rótulos de consenso da
amostra-ouro (`validacao/consenso_repositorios.csv`) e está disponível para os
60 repositórios sorteados.

Para as 24 combinações fator-métrica, foi aplicado Kruskal-Wallis. Os
24 p-valores foram corrigidos juntos pelo método de Holm. ε² é reportado como
H/(n−1), conforme definido no planejamento. Cliff's δ e a interpretação de
magnitude de Romano estão calculados para todos os pares de grupos nos arquivos
de saída; esses efeitos são descritivos, não testes post-hoc.

**Tabela RQ06.** Combinações com p < 0,05 após correção de Holm.

| Fator | Métrica | n | H | p ajustado (Holm) | ε² |
|---|---|---:|---:|---:|---:|
| Linguagem | Frequência | 298 | 39,44 | 0,0088 | 0,133 |
| Linguagem | Lead time por release | 298 | 51,94 | < 0,001 | 0,175 |
| Linguagem | CFR por releases | 297 | 47,67 | < 0,001 | 0,161 |
| Quartil de estrelas | Lead time por commit | 306 | 18,46 | 0,0060 | 0,061 |
| Quartil de idade | Frequência | 306 | 23,85 | < 0,001 | 0,078 |
| Quartil de idade | Lead time por release | 306 | 67,35 | < 0,001 | 0,221 |
| Quartil de idade | Lead time por commit | 306 | 68,81 | < 0,001 | 0,226 |
| Quartil de idade | CFR por releases | 305 | 31,13 | < 0,001 | 0,102 |
| Quartil de idade | Recuperação | 284 | 22,60 | < 0,001 | 0,080 |

Os padrões por idade não são monotônicos em todas as métricas. A mediana da
frequência cai de 0,537 releases/semana no quartil mais jovem para 0,288 no
mais antigo; os medianos de lead time crescem do Q1 até o Q3 e recuam no Q4.
O CFR por releases é mais alto no Q1 (0,500) do que nos demais quartis
(0,195–0,216). Os projetos mais jovens publicam mais releases e, com isso,
mais releases ficam a menos de sete dias de uma corretiva, o mesmo mecanismo
da correlação da RQ 05. A associação estatística entre idade e desempenho não deve ser
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

Para tipo do projeto, nenhum dos seis testes foi significativo após Holm
(n=60 para as cinco métricas sem valores ausentes; n=56 para recuperação).
Os rótulos de consenso se distribuem em aplicação/serviço (25), biblioteca/
framework (21), ferramenta CLI (11) e outro (3). O menor p-valor bruto foi o
da recuperação (p=0,0039; p ajustado 0,059; ε²=0,24). Bibliotecas e
frameworks tiveram mediana de 10,5 horas, contra 3,2 a 3,5 horas de aplicações
e ferramentas CLI, mas a diferença não resiste à correção para 24 testes. Com
60 repositórios e a categoria `outro` com só três itens, o poder da comparação
é baixo, e a ausência de significância não demonstra equivalência entre tipos.
Na análise provisória, feita só com os 47 rótulos unânimes, o resultado também
foi nulo nos seis testes.

## RQ 07 — Sensibilidade às definições operacionais

C1 é a referência (releases principais, lead time por release e CFR por CI).
Conforme o exemplo do enunciado, C2 inclui pré-releases na frequência e usa
lead time por commit e CFR por releases; C3 usa tags (datadas pelo commit
apontado), lead time por commit e CFR por CI. O tempo de recuperação permanece
igual nas três combinações. As categorias gerais usam os pares completos de
classificações disponíveis em cada comparação.

**Tabela RQ07.** Mudança da categoria geral e kappa ponderado linear.

| Par | n | Mudaram de categoria | % que mudou | κ ponderado |
|---|---:|---:|---:|---:|
| C1 × C2 | 283 | 108 | 38,2% | 0,415 |
| C1 × C3 | 284 | 60 | 21,1% | 0,714 |
| C2 × C3 | 283 | 100 | 35,3% | 0,500 |

Na categoria de frequência, 25/306 repositórios mudaram entre C1 e C2 (8,2%),
58/306 entre C1 e C3 (19,0%) e 33/306 entre C2 e C3 (10,8%). Em C1×C2, além
da frequência, a troca simultânea para lead time por commit e CFR por releases
contribui para a grande mudança na categoria geral; o CFR por releases troca
210/305 categorias (68,9%) em relação ao CFR por CI (eram 237/305, 77,7%, com
a heurística v1). C1×C3 também troca o
lead time para a variante por commit (115/306 categorias, 37,6%), além da
frequência.

Assim, as conclusões são sensíveis às definições combinadas, em especial ao
proxy de CFR. Pela escala de Landis e Koch, a concordância geral é moderada
para C1×C2 (κ=0,415) e C2×C3 (κ=0,500) e substancial para C1×C3 (κ=0,714).
Não é correto afirmar robustez alta para todos os pares. A troca da heurística
v1 pela v2 aumentou um pouco a concordância dos pares que envolvem C2, mas a
conclusão não muda: o proxy de CFR é a escolha que mais desloca a
classificação.

## Limitações

Os testes não controlam confundidores, os quartis refletem esta amostra
específica e grupos raros de linguagem têm poucas observações. A correção de
Holm reduz falsos positivos nas 24 comparações globais, mas não transforma
associações em relações causais. O CFR por releases depende da heurística v2,
que tem F1 de 0,59 na metade de teste da amostra-ouro, abaixo da meta de 0,70.
As associações com essa métrica (linguagem e idade) podem refletir, em parte,
diferenças na forma de escrever notas de release entre comunidades, e não só
diferenças de falha. O tipo do projeto só está disponível para os 60
repositórios da amostra-ouro.
