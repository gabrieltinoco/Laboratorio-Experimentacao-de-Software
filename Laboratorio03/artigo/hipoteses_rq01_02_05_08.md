# Hipóteses para a introdução (RQ 01, 02, 05 e 08)

Estas expectativas foram registradas antes da análise dos resultados. São
hipóteses de trabalho, não conclusões sobre os repositórios da amostra.

## RQ 01 — Frequência de deploy

Espera-se que a mediana fique entre uma release por mês e uma por semana,
ou seja, na faixa Medium da tabela de referência. Projetos open-source
populares costumam publicar releases em ciclos planejados, e a release
publicada no GitHub é um evento mais raro que o deploy contínuo de um
serviço. Também se espera uma distribuição muito assimétrica: poucos
repositórios com publicação automatizada (por exemplo, uma release por
merge ou *nightly*) devem chegar à faixa Elite e alongar a cauda superior.

## RQ 02 — Lead time

Espera-se que a mediana do lead time por commit (b) fique entre uma semana
e um mês, já que um commit espera, em média, metade do intervalo entre duas
releases. Espera-se também que a variante por release (a) seja maior que a
(b) na maioria dos repositórios: ela usa o commit mais antigo de cada
release, e um único commit antigo, vindo de um branch de longa duração ou
de um *cherry-pick*, basta para elevá-la. Rebases e *squash merges*
preservam a data de autoria original e devem reforçar essa diferença.

## RQ 05 — Frequência de deploy × taxa de falha

Com o CFR (a), espera-se correlação fraca, próxima de zero ou levemente
negativa: projetos que publicam com mais frequência tendem a ter pipelines
mais maduros, o que está em linha com a afirmação do DORA de que velocidade
e estabilidade não competem. Com o CFR (b), espera-se correlação positiva:
quanto mais releases um projeto publica, maior a chance de uma release
corretiva cair nos sete dias seguintes a outra, mesmo sem mais defeitos.
Nos dois casos, a correlação não indica causalidade.

## RQ 08 — Rework rate (bônus)

Espera-se que o rework rate seja maior que o CFR (b) na maioria dos
repositórios. O rework conta toda release corretiva, enquanto o CFR (b) só
conta a release anterior quando a correção sai em até sete dias. Como a
heurística v1 também marca como corretiva qualquer release com um commit
`fix`, espera-se ainda um rework rate alto em termos absolutos, o que
mostraria mais a sensibilidade da heurística que retrabalho de fato.
