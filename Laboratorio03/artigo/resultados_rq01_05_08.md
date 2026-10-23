# Resultados e Discussão: RQ 01 a RQ 05 e RQ 08

Tabelas e figuras geradas por `python -m analise.comum`, `python -m analise.rq01_04`
e `python -m analise.rq05_rq08` a partir de `dados/repositorios.csv` (306
repositórios). Todos os valores são mediana e IQR (Q1–Q3). A classificação DORA
é a de referência (C1: release, lead time (a), CFR (a)).

**Tabela R1.** Métricas DORA da amostra.

| Métrica | n | Mediana | Q1 | Q3 |
|---|---:|---:|---:|---:|
| Frequência de deploy (releases/semana) | 306 | 0,345 | 0,192 | 0,743 |
| Lead time (a) por release (dias) | 306 | 13,98 | 3,01 | 33,94 |
| Lead time (b) por commit (dias) | 306 | 12,24 | 3,44 | 47,52 |
| CFR (a) proxy de CI | 306 | 0,065 | 0,023 | 0,122 |
| CFR (b) proxy de entrega | 305 | 0,250 | 0,091 | 0,540 |
| Tempo de recuperação (horas) | 284 | 3,75 | 0,93 | 14,95 |

**Tabela R2.** Distribuição das categorias DORA (C1), em % dos repositórios classificados.

| Métrica | n | Elite | High | Medium | Low |
|---|---:|---:|---:|---:|---:|
| Frequência de deploy | 306 | 1,3 | 19,0 | 46,1 | 33,7 |
| Lead time (a) | 306 | 14,4 | 22,2 | 35,3 | 28,1 |
| CFR (a) | 306 | 80,4 | 11,4 | 4,6 | 3,6 |
| Tempo de recuperação | 284 | 26,8 | 58,1 | 10,6 | 4,6 |
| **Geral** | 284 | 7,0 | 37,0 | 49,3 | 6,7 |

A classificação geral exige as quatro métricas. Os 22 repositórios sem tempo de
recuperação (20 sem nenhum episódio de falha e 2 só com episódios censurados)
ficam sem categoria geral.

## RQ 01 — Frequência de deploy

A mediana é de 0,345 release por semana, cerca de uma release a cada três
semanas (IQR 0,19–0,74). A distribuição é muito assimétrica (Figura R1): poucos
repositórios passam de uma release por semana, e só 4 (1,3%) chegam à faixa
Elite. Quase metade (46,1%) fica em Medium e um terço (33,7%) publica menos de
uma release por mês. Isso confirma a hipótese: a release publicada no GitHub é
um evento planejado, bem mais raro que o deploy contínuo de um serviço.

## RQ 02 — Lead time

As medianas das duas variantes ficam próximas, 14,0 dias para a (a) e 12,2
para a (b), ambas na faixa Medium, o que confirma a hipótese para a variante
(b). A hipótese de que (a) seria maior que (b) na maioria dos repositórios só se
confirmou em parte: (a) > (b) em 59,8% dos repositórios, e a razão (a)/(b) tem
mediana 1,23, mas IQR de 0,50 a 2,11. A variante (b) tem a cauda superior mais
longa (Q3 de 47,5 contra 33,9 dias).

As duas divergem por razões opostas. A (a) explode quando uma release inclui um
único commit antigo, vindo de um branch de longa duração ou de um
*cherry-pick*. Na (b), esse commit é só mais um valor e quase não move a
mediana. Por outro lado, a (b) dá a cada commit o mesmo peso, então as
releases grandes, que acumulam muitos commits ao longo de semanas, dominam a
mediana do repositório. Na (a), cada release conta uma vez, e as releases
pequenas e frequentes puxam o valor para baixo. A escolha da variante muda a
categoria de parte dos repositórios, e isso é tratado na RQ 07.

## RQ 03 — Taxa de falha

O CFR (a), proxy de CI, tem mediana de 6,5% (IQR 2,3%–12,2%), e 80,4% dos
repositórios ficam em Elite. O CFR (b), proxy de entrega, tem mediana de 25,0%
(IQR 9,1%–54,0%), quase quatro vezes maior. A hipótese de que o CFR (a) seria
maior que o (b) não se confirmou.

As duas variantes medem coisas diferentes. Um run de CI que falha no *default
branch* é uma falha de pipeline: costuma ser um teste instável ou uma quebra
corrigida no commit seguinte, sem chegar ao usuário. O CFR (b) é mais próximo
da definição DORA, porque exige uma release corretiva publicada, mas depende da
heurística de release corretiva. Os valores acima usam a v2, que na metade de
teste da amostra-ouro tem precisão de 0,50 e recall de 0,73 (F1 0,59). A v1
marcava como corretiva qualquer release com um commit `fix` e dava mediana de
33,3%. A queda para 25,0% com a v2 indica quanto a v1 inflava a métrica. Como a
v2 ainda produz cerca de um falso positivo para cada verdadeiro positivo, o
CFR (b) deve ser lido como limite superior aproximado, e não como taxa de falha
medida.

## RQ 04 — Tempo de recuperação

A mediana é de 3,7 horas (IQR 0,9–14,9 horas): 84,9% dos repositórios se
recuperam em menos de um dia (Elite ou High), o que confirma a hipótese. A
censura foi rara: dos 15.709 episódios de falha, 107 (0,7%) não terminaram
dentro da janela, mas eles aparecem em 68 repositórios (22%). Como só os
episódios encerrados entram na mediana, esses repositórios podem estar
parecendo mais rápidos do que são. Com 0,7% dos episódios, o efeito na mediana
geral é pequeno.

## RQ 05 — Frequência de deploy × taxa de falha

**Tabela R3.** Correlação de Spearman entre frequência de deploy e CFR.

| Par | ρ | p-valor | n |
|---|---:|---:|---:|
| Frequência × CFR (a) | 0,134 | 0,019 | 306 |
| Frequência × CFR (b) | 0,679 | < 0,001 | 305 |

Com o CFR (a), a correlação é positiva, mas fraca (ρ = 0,13): a frequência
explica muito pouco da ordem dos repositórios por taxa de falha de CI (Figura
R2). A hipótese previa correlação nula ou levemente negativa. O sinal ficou
contrário, mas a força é tão baixa que o resultado não sustenta um *trade-off*
entre velocidade e estabilidade. Com o CFR (b), a correlação é forte
(ρ = 0,68), como previsto. Com a v1 da heurística ela era 0,73, então quase
toda a correlação sobrevive à heurística mais restritiva. Boa parte dela é mecânica: quanto mais releases um
projeto publica, menor o intervalo entre elas e maior a chance de uma release
corretiva cair nos sete dias seguintes a outra.

Os dados não confirmam a afirmação do DORA de que as equipes mais rápidas
também são as mais estáveis, mas também não a contradizem com segurança. O
proxy de CI não mostra relação relevante, e o proxy de entrega tem uma relação
forte que vem, em boa parte, da própria definição. Correlação não implica
causalidade em nenhum dos casos.

## RQ 08 (bônus) — Rework rate

O rework rate, proporção de releases corretivas sobre o total de releases da
janela, tem mediana de 0,542 (IQR 0,344–0,729) com a heurística v2. Ele é
maior que o CFR (b) em 70,2% dos repositórios (diferença mediana de 0,18;
Wilcoxon pareado, p < 0,001), e as duas métricas têm correlação positiva e
fraca (ρ = 0,30).

As duas diferem na definição. O rework conta cada release corretiva. O CFR (b)
conta a release *anterior* a uma corretiva, e só quando a correção sai em até
sete dias. Uma correção lenta entra no rework, mas não no CFR (b), o que
explica o rework maior na maioria dos repositórios.

Com a v1, o rework tinha mediana de 0,976 e correlação negativa com o CFR (b)
(ρ = −0,23). Quase toda release tinha algum commit com `fix`, `hotfix`,
`revert` ou `bugfix`, e a métrica media a presença de alguma correção, não o
objetivo da release. A amostra-ouro confirmou essa hipótese: a v1 tem precisão
de 0,38. Com a v2, o rework passa a variar entre repositórios e se alinha com
o CFR (b). Mesmo assim, a mediana de 0,54 ainda é alta. A amostra-ouro tem
35,7% de releases corretivas, e a precisão de 0,50 da v2 sugere que o rework
real fica abaixo do medido. A comparação entre as duas métricas é mais
confiável que o valor absoluto de cada uma.
