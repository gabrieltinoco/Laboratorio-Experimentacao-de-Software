# Ameaças à validade

As ameaças seguem as quatro categorias de Wohlin et al. [2012]. Sempre que
possível, cada uma é dimensionada com a validação manual (amostra-ouro de 60
repositórios e 300 releases) ou com a análise de sensibilidade da RQ 07.

## Validade de construto

**Release não é deploy.** Toda a análise trata uma release publicada no GitHub
como deploy. Para bibliotecas, a release coincide com a publicação do pacote.
Para serviços, o deploy em produção pode acontecer sem release, ou muito depois
dela. A amostra-ouro reduz parte dessa dúvida: nenhum dos 60 repositórios teve
as releases rotuladas como "não são entregas reais", e só 4 ficaram como
`incerto`. Mesmo assim, a frequência medida é a de *releases* e subestima o
ritmo de deploy de quem entrega continuamente. O funil mostra outro lado do
problema: 570 dos 658 descartes na etapa de inclusão foram por falta de
releases, então os projetos que não usam releases do GitHub ficaram fora da
amostra.

**A variante muda a categoria.** A RQ 07 mostra que a definição operacional
altera a classificação. Trocar o CFR por CI pelo CFR por releases muda a
categoria de CFR de 68,9% dos repositórios. A categoria geral muda em 38,2%
deles entre C1 e C2 (κ ponderado 0,415) e em 21,1% entre C1 e C3 (κ 0,714). Os
números absolutos de cada métrica valem só para a definição escolhida, e as
categorias DORA são comparadas com cautela.

**CFR (a) mede falha de CI, não falha em produção.** Um run vermelho no
*default branch* costuma ser teste instável ou quebra de build, e não um
incidente com usuário. Isso explica parte da distância entre o CFR (a), com
mediana de 6,5%, e o CFR (b), com mediana de 25,0%.

**A heurística corretiva tem erro conhecido.** O CFR (b) e o rework rate
dependem da heurística de release corretiva. A v1 teve precisão de 0,38
contra o consenso humano e inflava as duas métricas: o rework tinha mediana de
0,98. A v2 tem, na metade de teste, precisão de 0,50, recall de 0,73 e F1 de
0,59, abaixo da meta de 0,70. Por isso, o CFR (b) e o rework devem ser lidos
como *proxies* com cerca de um falso positivo por verdadeiro positivo, e não
como taxas de falha.

**Datas de commit.** O lead time usa `commit.author.date`. *Rebase* e *squash*
podem alterar essa data, e *cherry-picks* antigos inflam o lead time por
release (RQ 02). As duas variantes de lead time foram reportadas justamente
porque reagem de forma diferente a esses casos.

## Validade interna

**Idade e volume de releases estão confundidos.** Os repositórios do quartil
mais jovem publicam mais releases (0,54 contra 0,29 por semana no quartil mais
antigo) e têm CFR (b) mais alto (0,50 contra cerca de 0,20). Mais releases
encurtam o intervalo entre elas e aumentam a chance de uma corretiva cair nos
sete dias seguintes. Assim, a correlação entre frequência e CFR (b) (ρ = 0,68)
e a associação entre idade e CFR (b) são, em parte, efeitos mecânicos da
definição, e não evidência de que equipes mais rápidas falham mais.

**Os fatores não foram controlados.** A RQ 06 testa cada fator isoladamente.
Linguagem, idade, popularidade e tipo do projeto se correlacionam entre si, e
os testes não ajustam um pelo outro.

**A forma de escrever as notas interfere na métrica.** A v2 depende das notas
de release. Comunidades que escrevem notas com seções padronizadas
(*Bug Fixes*, *Features*) são classificadas com mais precisão do que as que
escrevem em prosa ou deixam as notas vazias. Parte das diferenças de CFR (b)
entre linguagens pode refletir esse costume, e não a taxa real de falha.

**Censura e teto da API.** Episódios de falha que não terminaram na janela
(0,7% do total) ficam fora da mediana de recuperação. As releases dos últimos
sete dias saem do denominador do CFR (b). Em 35 repositórios, algum mês atingiu
o teto de 1.000 workflow runs por consulta, e as métricas de CI desses meses
podem estar subestimadas.

**O consenso foi feito com assistência de IA.** As 43 divergências entre os
avaliadores foram decididas com apoio de um assistente de IA, que aplicou os
critérios escritos do protocolo às evidências de cada item, e não em reunião
entre os dois avaliadores. As justificativas estão registradas item a item em
`divergencias.csv`. O efeito se limita a 43 dos 420 rótulos (10%): 13 tipos de
projeto, 9 rótulos de entrega e 21 de corretividade. Em corretividade, o
consenso decidiu `sim` em 7 dos 21 casos. O kappa reportado é o da rotulação
independente, feita antes do consenso.

## Validade externa

**A amostra é de projetos populares e abertos.** Ela tem repositórios com pelo
menos 1.000 estrelas, que usam GitHub Actions e publicam releases. Projetos
corporativos, privados ou que entregam por outros canais podem ter perfis
diferentes.

**A busca favorece os mais populares.** A busca do GitHub devolve no máximo
1.000 resultados por consulta. Nas faixas baixas de estrelas, só os
repositórios mais populares de cada faixa foram alcançados (7.451 de 37.401
candidatos). O embaralhamento com semente fixa reduz, mas não elimina, esse
viés.

**O resultado vale para uma janela de 12 meses.** A janela vai de outubro de
2025 a setembro de 2026, e o dataset é uma fotografia desse período.
Repositórios continuam recebendo commits e releases, e uma coleta em outra data
pode dar valores diferentes, como prevê a replicação cruzada.

## Validade de conclusão

**Muitas comparações.** A RQ 06 faz 24 testes de Kruskal-Wallis. Os p-valores
foram corrigidos juntos pelo método de Holm, e os Cliff's δ entre pares são
apresentados só como descrição, sem testes *post-hoc*.

**Alguns subgrupos são pequenos.** Várias linguagens têm menos de cinco
repositórios (HTML 2, Vue 2, Ruby 3, Shell 4). Para o tipo do projeto há
apenas 60 repositórios, com só 3 na categoria `outro`. Nesses casos, um
resultado sem significância não demonstra equivalência. A recuperação por tipo,
por exemplo, teve p bruto de 0,004, mas p ajustado de 0,059.

**A concordância entre avaliadores varia por dimensão.** Ela foi quase
perfeita para corretividade (κ = 0,85), substancial para tipo do projeto
(κ = 0,69) e moderada para entregas reais (κ = 0,41). Com dois avaliadores, não
houve desempate por maioria.

**A heurística foi escolhida com dados da própria amostra-ouro.** As regras da
v2 foram comparadas em metade dos repositórios da amostra-ouro, e o desempenho
foi reportado na outra metade. Com 150 releases e 40 corretivas na metade de
teste, a estimativa de F1 (0,59) tem incerteza considerável, e a metade de
teste não pode ser reutilizada para escolher uma v3.

## Referência

- Wohlin, C.; Runeson, P.; Höst, M.; Ohlsson, M. C.; Regnell, B.; Wesslén, A.
  (2012). *Experimentation in Software Engineering*. Springer.
