# Hipóteses para a introdução

Estas expectativas foram registradas antes da análise dos resultados. São
hipóteses de trabalho, não conclusões sobre os repositórios da amostra.

## RQ 03 — Taxa de falha

Espera-se que o proxy baseado em falhas de workflow seja maior que o proxy
baseado em releases seguidas por uma release corretiva. O primeiro contabiliza
falhas de CI diretamente, enquanto o segundo exige uma correção publicada em
até sete dias; portanto, os dois proxies devem produzir estimativas diferentes
e representar fenômenos distintos.

## RQ 04 — Tempo de recuperação

Espera-se que a mediana do tempo entre a primeira falha e a execução bem-sucedida
seguinte seja inferior a 24 horas. Ainda assim, é provável que existam episódios
censurados, pois algumas falhas podem permanecer sem recuperação observável até
o fim da janela.

## RQ 06 — Características associadas ao desempenho

Espera-se que as distribuições das métricas variem entre pelo menos alguns dos
subgrupos de linguagem, popularidade, número de contribuidores, idade e tipo de
projeto. Em particular, repositórios com mais estrelas e contribuidores são
esperados apresentar maior frequência de releases; não se pressupõe que essa
maior atividade implique menor taxa de falha ou recuperação mais rápida.

## RQ 07 — Sensibilidade às definições operacionais

Espera-se que pelo menos uma alteração da definição de referência C1
(releases, lead time por release e CFR por CI) mude a categoria DORA de parte
dos repositórios. A inclusão de pré-releases em C2 deve produzir mais mudanças
que a troca de releases por tags em C3, pois altera diretamente a unidade e a
frequência observadas. Assim, prevê-se concordância ponderada inferior a 1 em
pelo menos uma comparação entre combinações.
