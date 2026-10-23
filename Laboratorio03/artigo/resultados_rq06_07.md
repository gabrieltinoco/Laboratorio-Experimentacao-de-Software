# Resultados e Discussão: RQ 06 e RQ 07

As análises foram executadas sobre `dados/repositorios.csv` (306
repositórios). O script `python -m analise.rq06_rq07` gera as tabelas
detalhadas em `analise/saidas/`.

## RQ 06 — Características associadas ao desempenho

Foram comparadas seis métricas (frequência de deploy, lead time por release,
lead time por commit, CFR por CI, CFR por releases e recuperação) em quatro
fatores: linguagem principal, quartis de estrelas, quartis de idade e tipo do
projeto. Os quartis foram formados por postos, para manter quatro grupos de
tamanhos semelhantes. Ainda há 13 divergências de tipo do projeto sem decisão
conjunta; por isso, o fator foi analisado apenas nos 47 repositórios em que os
dois avaliadores atribuíram o mesmo rótulo. Os itens divergentes não receberam
rótulo de consenso inventado e foram excluídos desta comparação provisória.

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
| Linguagem | CFR por releases | 297 | 40,06 | 0,0075 | 0,135 |
| Quartil de estrelas | Lead time por commit | 306 | 18,46 | 0,0064 | 0,061 |
| Quartil de idade | Frequência | 306 | 23,85 | 0,0005 | 0,078 |
| Quartil de idade | Lead time por release | 306 | 67,35 | < 0,001 | 0,221 |
| Quartil de idade | Lead time por commit | 306 | 68,81 | < 0,001 | 0,226 |
| Quartil de idade | CFR por releases | 305 | 51,06 | < 0,001 | 0,168 |
| Quartil de idade | Recuperação | 284 | 22,60 | 0,0009 | 0,080 |

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

Para tipo do projeto, nenhum dos seis testes foi significativo após Holm
(n=47 para as cinco métricas sem valores ausentes; n=42 para recuperação).
Os rótulos unânimes se distribuem em aplicação/serviço (17), biblioteca/
framework (20), ferramenta CLI (8) e outro (2). A categoria `outro` tem
somente dois itens, limitando o poder da comparação. A ausência de significância
não demonstra equivalência entre tipos.

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
| C1 × C2 | 283 | 115 | 40,6% | 0,388 |
| C1 × C3 | 284 | 60 | 21,1% | 0,714 |
| C2 × C3 | 283 | 118 | 41,7% | 0,428 |

Na categoria de frequência, 25/306 repositórios mudaram entre C1 e C2 (8,2%),
58/306 entre C1 e C3 (19,0%) e 33/306 entre C2 e C3 (10,8%). Em C1×C2, além
da frequência, a troca simultânea para lead time por commit e CFR por releases
contribui para a grande mudança na categoria geral; o CFR por releases troca
237/305 categorias (77,7%) em relação ao CFR por CI. C1×C3 também troca o
lead time para a variante por commit (115/306 categorias, 37,6%), além da
frequência.

Assim, as conclusões são sensíveis às definições combinadas, em especial ao
proxy de CFR. Pela escala de Landis e Koch, a concordância geral vai de
razoável (κ=0,388) e moderada (κ=0,428) a substancial (κ=0,714); não é correto
afirmar robustez alta para todos os pares.

## Limitações e pendências

Os dois avaliadores já preencheram as planilhas. A concordância foi calculada:
tipo do projeto teve 78,33% de concordância observada e κ de Cohen 0,6923;
entregas reais, 85,00% e κ=0,4105; corretividade, 93,00% e κ=0,8496. Restam
43 divergências para a reunião de consenso: 13 de tipo do projeto, 9 de
entregas reais e 21 de corretividade. Até que sejam decididas e registradas,
os resultados da RQ06 por tipo são apenas sobre os 47 itens unânimes, e a
avaliação final P/R/F1 da heurística não pode ser calculada legitimamente.

Além disso, os testes não controlam confundidores, os quartis refletem esta
amostra específica e grupos raros de linguagem têm poucas observações. A
correção de Holm reduz falsos positivos nas 24 comparações globais, mas não
transforma associações em relações causais. O CFR por releases depende da
heurística cuja validação humana ainda está pendente.
