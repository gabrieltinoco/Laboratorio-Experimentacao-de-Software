## INFORMAÇÕES SOBRE A AVALIAÇÃO
| LAB02 | Laboratório 02 - 20 pontos |
|---|---|

### INFORMAÇÕES DOCENTE
| CURSO: ENGENHARIA DE SOFTWARE | DISCIPLINA: LABORATÓRIO DE EXPERIMENTAÇÃO DE SOFTWARE | TURNO: NOITE | PERÍODO/SALA: 6º|
|---|---|---|---|

**PROFESSOR(A):** Danilo Maia
---
## Assistentes de IA vs. Codificação Manual: um experimento controlado
Ferramentas de IA generativa (GitHub Copilot, ChatGPT, Claude, Gemini etc.)
tornaram-se onipresentes no desenvolvimento de software, mas ainda há pouca
evidência controlada e reproduzível sobre seu real impacto em produtividade e
qualidade — a maior parte do que se ouve é relato anedótico. Neste laboratório,
o objetivo é realizar um experimento controlado para avaliar quantitativamente
os efeitos do uso de um assistente de IA na resolução de tarefas de programação.

### Parte 1 — Questões de Pesquisa

**RQ 01.** O uso de assistente de IA reduz o tempo necessário para resolver uma
tarefa de programação?
Métrica: tempo até passar em todos os testes de aceitação ("time-to-green")

**RQ 02.** O uso de assistente de IA reduz a quantidade de defeitos (testes que
falham) no código produzido?
Métrica: testes de aceitação passando ao final do time-box

**RQ 03.** O uso de assistente de IA altera a complexidade ciclomática ou a
duplicação do código produzido?
Métrica: complexidade ciclomática e percentual de duplicação do código final
*(métricas via CK — apenas Java — e/ou PMD; usar ferramenta equivalente, como
Radon, se a linguagem escolhida não for Java)*

### Parte 2 — GQM (Goal-Question-Metric) e métricas

**Goal:** analisar o uso de assistentes de IA generativa na resolução de tarefas
de programação, com o propósito de comparar seu efeito frente à codificação
manual, com respeito a tempo de resolução, qualidade funcional (defeitos) e
qualidade estrutural do código produzido, do ponto de vista do grupo
pesquisador, no contexto de katas de dificuldade equivalente resolvidos por
estudantes de graduação sob condições controladas (crossover within-subject,
time-boxed).

As RQs 01, 02 e 03 são as *Questions* do GQM. Cabe ao grupo escolher, entre as
métricas candidatas abaixo, quais usar para responder cada RQ — a escolha e a
justificativa devem constar no Desenho do Experimento (Passo 1) e no Relatório
Final.

**RQ 01 — Tempo (métricas candidatas)**
1. Tempo até passar em todos os testes de aceitação ("time-to-green") — métrica
primária recomendada.
2. Trial que atinge o time-box (35 min) sem sucesso deve ser registrado como
**censurado em 35 min**, não descartado — descartar distorce a comparação a
favor do tratamento com mais falhas.
3. Métrica agregada recomendada: **mediana** por tratamento (não a média), dado
o N pequeno (4-6 trials por integrante) e a sensibilidade da média a outliers.
4. Opcional/exploratória: nº de prompts/interações com o assistente de IA — não
obrigatória, mas útil para a discussão qualitativa.

**RQ 02 — Defeitos (métricas candidatas)**
1. Taxa de sucesso: % de testes de aceitação passando ao final do time-box —
mais robusta que a contagem bruta, pois normaliza katas com números diferentes
de testes.
2. Nº absoluto de testes falhando ao final do tempo — métrica complementar, mais
simples de reportar.
3. Opcional: densidade de defeitos (testes falhando / KLOC), para comparar katas
de tamanhos bem diferentes.

**RQ 03 — Estrutura do código (métricas candidatas)**
1. Complexidade ciclomática média (McCabe) por método/função — CK (Java, métrica
WMC/complexity) ou Radon `cc` (Python).
2. Duplicação de código: % de linhas duplicadas via PMD CPD (Java) ou ferramenta
equivalente (ex.: `jscpd` para Python/JS, se o Radon não cobrir duplicação).
3. LOC (linhas de código) como métrica de controle — **obrigatória** sempre que
reportar complexidade/duplicação: código gerado por IA pode ser mais verboso, e
complexidade/duplicação sem normalizar por LOC pode enganar.
4. Opcional (aprofundamento): Índice de Manutenibilidade (Radon `mi`) — métrica
composta (complexidade + LOC + volume de Halstead), mais robusta que olhar cada
métrica isoladamente.

**Robustez estatística:** dado o tamanho amostral reduzido, prefira **mediana e
IQR** (intervalo interquartil) a média e desvio-padrão nas tabelas e gráficos
descritivos, e mantenha o **teste de Wilcoxon** (não paramétrico) na análise
inferencial do Passo 4 — consistente com o desenho within-subject.

### Parte 3 — Etapas esperadas do experimento

**Passo 1 — Desenho do Experimento.** Defina, no mínimo: (A) hipóteses nula e
alternativa; (B) variáveis dependentes (tempo, nº de testes passando, métricas
estáticas); (C) variável independente (uso ou não do assistente de IA); (D)
tratamentos; (E) objetos experimentais (conjunto de katas de dificuldade
equivalente); (F) tipo de projeto experimental (recomenda-se
crossover/within-subject, contrabalanceado, para controlar variação individual
de habilidade); (G) quantidade de medições; (H) ameaças à validade (efeito de
aprendizado entre katas, familiaridade prévia com a ferramenta de IA, vazamento
de solução já vista e memorização — se as katas forem muito conhecidas, ex.:
exercícios clássicos do LeetCode/HackerRank, o assistente de IA pode reproduzir
uma solução já vista em seu treinamento em vez de efetivamente "ajudar"; para
reduzir esse risco, prefira katas autorais do grupo/professor ou exercícios
pouco indexados).

**Passo 2 — Preparação do Experimento.** Escolha de **4 ou 6 katas** de
dificuldade comparável — número par, para permitir a divisão exata pela metade
entre trials com e sem assistente de IA — com testes automatizados de aceitação.
Prepare o ambiente (linguagem, IDE, assistente de IA a ser usado,
cronômetro/registro de tempo, scripts de coleta das métricas estáticas). O grupo
deve usar o **mesmo assistente de IA em todos os trials**, para que o tratamento
seja comparável dentro do próprio experimento (ex.: GitHub Copilot gratuito via
GitHub Student Developer Pack, ou a versão gratuita de um chatbot como
ChatGPT/Claude/Gemini). Fixe também a linguagem de programação das katas de
acordo com a ferramenta de métricas estáticas escolhida (CK exige Java; para
outras linguagens, use uma ferramenta equivalente, como Radon para Python).

**Passo 3 — Execução do Experimento.** Cada integrante resolve metade dos katas
com assistente de IA habilitado e a outra metade sem, em **ordem
contrabalanceada entre os integrantes**, sob **time-box de 35 minutos por
trial** (o grupo pode reduzir esse limite e justificar no relatório, mas **não
pode aumentá-lo**, para manter a comparabilidade entre grupos da turma). Ao
final do tempo, o trial é encerrado independentemente do resultado. Registre:
tempo até passar nos testes de aceitação (ou até o fim do time-box), nº de
testes passando ao final do tempo, e execute CK/PMD (ou equivalente) sobre o
código final de cada trial.

**Passo 4 — Análise de Resultados.** Revise os dados coletados, identifique
outliers e aplique os testes estatísticos adequados (teste de Wilcoxon para
amostras pareadas, dado o desenho within-subject).

**Passo 5 — Relatório Final.** Ver a seção "Relatório Final" abaixo.

**Passo 6 — Dashboard de Visualização.** Importe os dados do experimento e gere
gráficos (Pandas + Matplotlib/Seaborn) comparando tempo, taxa de sucesso e
métricas estáticas entre os tratamentos.

### Relatório Final
Documento com: (i) introdução com as hipóteses; (ii) metodologia detalhada o
suficiente para permitir reprodução/replicação (ambiente, katas usados,
assistente de IA e versão); (iii) resultados por RQ com as respostas
estatísticas obtidas; (iv) discussão final; (v) o link do repositório/GitHub
Projects do grupo.
Link do repositório: https://github.com/gabrieltinoco/Laboratorio-Experimentacao-de-Software
Link do GitHub Projects: https://github.com/users/gabrieltinoco/projects/2

### Processo de Desenvolvimento

**Contribuição individual por sprint:** em toda sprint (S01, S02 e S03), cada
integrante do trio deve ser **Assignee** de ao menos uma Issue com artefato de
código commitado (script, notebook, gráfico ou trial de kata) — não apenas nas
Issues de execução de katas da S02. A ausência de commits atribuíveis a um
integrante em uma sprint **zera** a parcela individual daquele integrante na
sprint.

**Lab02S01** (5 pontos): Desenho do experimento + preparação (Passos 1-2: katas
escolhidos, ambiente, scripts de medição de tempo e de métricas estáticas). Os
cartões do desenho e da preparação devem estar no Kanban do grupo.
*Divisão sugerida por integrante (não obrigatória — o trio é livre para se
organizar de outra forma, desde que a regra de contribuição individual acima
seja respeitada):*
- **Integrante A — cronometragem e coleta de tempo:** escreve o script que
registra o tempo de cada trial (time-to-green), incluindo o corte automático em
35 min (censura, não descarte) e a exportação dos dados brutos (CSV/JSON) com
colunas para integrante, kata, tratamento (com/sem IA), tempo e status final.
Define também o formato padrão de log usado pelos três na S02.
- **Integrante B — ambiente e métricas estáticas:** prepara o ambiente de
desenvolvimento (linguagem, IDE, versão do assistente de IA) e escreve os
scripts de coleta das métricas estáticas (CK se Java, ou Radon se outra
linguagem, mais PMD CPD/jscpd para duplicação), deixando-os prontos para rodar
sobre o código final de cada trial na S02.
- **Integrante C — katas e desenho experimental:** pesquisa e valida os 4 ou 6
katas de dificuldade comparável e baixa indexação (evitando exercícios clássicos
memorizáveis), redige as hipóteses nula/alternativa, define as variáveis
(dependentes/independente), o tipo de projeto experimental (crossover
within-subject contrabalanceado) e a seção de ameaças à validade.

Os três revisam o desenho completo em conjunto antes de fechar a sprint, e cada
um commita o seu artefato (script ou documento) referenciando a sua própria
Issue no board.

**Lab02S02** (5 pontos): Execução do experimento + coleta de dados (Passo 3).
*Divisão sugerida por integrante:* já naturalmente dividida pelo próprio desenho
— cada integrante resolve, individualmente, **todos** os katas escolhidos,
metade com assistente de IA habilitado e metade sem, em ordem contrabalanceada
entre os três (para não repetir a mesma sequência kata/tratamento). Cada trial
(kata × tratamento × integrante) vira uma **Issue individual** no GitHub
Projects, atribuída a quem executou, com o código final e os dados de
tempo/testes commitados referenciando o número da Issue — o que já garante
commits atribuíveis aos três na sprint, sem necessidade de divisão adicional de
papéis.

**Lab02S03** (5 pontos): Análise de resultados (Passo 4, cobrindo as RQs 01, 02
e 03) + Dashboard de Visualização (Passo 6).
*Divisão sugerida por integrante:*
- **Integrante A — estatística das RQs 01 e 02:** consolida os dados de tempo e
de taxa de sucesso/defeitos de todos os trials, identifica outliers, calcula
mediana e IQR por tratamento e aplica o teste de Wilcoxon pareado.
- **Integrante B — análise da RQ 03 (métricas estáticas):** roda CK/PMD (ou
Radon/jscpd) sobre o código final de todos os trials, calcula complexidade
ciclomática média, % de duplicação e LOC como controle, e aplica Wilcoxon também
para a RQ 03.
- **Integrante C — dashboard de visualização:** monta o dashboard em Pandas +
Matplotlib/Seaborn consolidando os três conjuntos de resultados (tempo,
sucesso/defeitos, métricas estáticas) em gráficos comparativos entre os
tratamentos, a partir dos dados e análises produzidos por A e B.

Cada um cria a sua própria Issue nesta sprint (script de análise, notebook ou
gráfico) e commita referenciando o número dela.

**Relatório Final** (5 pontos): elaboração do documento final (Passo 5 — ver
seção "Relatório Final" acima). Pode ser dividido entre os três
(introdução/hipóteses, metodologia, resultados/discussão), com revisão conjunta
antes da entrega, mantendo o link do repositório/GitHub Projects no documento
final.

**Prazo final:** conforme cronograma da disciplina.

**Valor total:** 20 pontos | Desconto de até 10% da nota da sprint por qualidade
insuficiente do uso do GitHub Projects (WIP não respeitado, Issues sem Assignee,
cartões desatualizados, ausência de evolução semanal).

**Observação:** o time-box de 35 min por trial é fixo — só pode ser reduzido,
nunca aumentado. Todos os trials devem ser registrados no GitHub Projects do
grupo como Issues individuais (uma por kata/tratamento), atribuídas ao integrante
responsável (campo Assignee), mantendo a rastreabilidade entre o experimento e o
board. A correção é feita a partir do GitHub Projects: commits sem referência ao
número da Issue correspondente não serão considerados.
