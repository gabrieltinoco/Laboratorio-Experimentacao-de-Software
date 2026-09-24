# Relatório Final — Assistentes de IA vs. Codificação Manual: um Experimento Controlado

- **Disciplina:** Laboratório de Experimentação de Software
- **Laboratório:** Lab02
- **Integrantes:** `<preencher>`
- **Repositório/GitHub Projects:** `<preencher>`

---

## 1. Introdução

Assistentes de IA generativa, como GitHub Copilot, ChatGPT, Claude e Gemini, passaram a
fazer parte do dia a dia de quem desenvolve software. Eles completam trechos de código,
sugerem funções inteiras e respondem dúvidas sem que a pessoa saia do editor. A adoção
foi rápida, mas a evidência sobre o efeito real dessas ferramentas ainda é, em grande
parte, anedótica: relatos de ganho de produtividade convivem com relatos de código mais
longo, mais difícil de manter ou com defeitos sutis que passam despercebidos.

Este trabalho mede esse efeito com um **experimento controlado**. Os integrantes
resolveram tarefas de programação curtas (katas) de dificuldade equivalente, metade com
o GitHub Copilot ativo e metade com a extensão desativada. Linguagem (Python), IDE
(VS Code), testes de aceitação (pytest), time-box de 35 minutos por trial e ambiente
foram mantidos iguais nos dois tratamentos. O desenho é **crossover within-subject
contrabalanceado**. Cada integrante é o seu próprio controle, e a ordem de katas e
tratamentos alterna entre sequências para diluir o efeito de aprendizado.

As quatro katas (`fila-prioridade`, `janela-cobranca`, `agenda-recorrente` e
`roteador-notificacoes`) foram escritas pelo grupo para esta pesquisa. Cada uma pede a
implementação de uma única função e tem oito testes de aceitação. Katas clássicas e muito indexadas,
como FizzBuzz ou Bowling, foram evitadas de propósito. Com elas, o experimento mediria
a memória do participante ou do modelo, e não a ajuda do assistente na resolução.

O objetivo, na forma do GQM (Goal-Question-Metric), é:

> **Analisar** o uso de assistentes de IA generativa na resolução de tarefas de
> programação, **com o propósito de** comparar seu efeito frente à codificação manual,
> **com respeito a** tempo de resolução, qualidade funcional (defeitos) e qualidade
> estrutural do código produzido, **do ponto de vista** do grupo pesquisador, **no
> contexto de** katas de dificuldade equivalente resolvidos por estudantes de graduação
> sob condições controladas (crossover within-subject, time-boxed).

### 1.1 Questões de pesquisa

- **RQ1 — Tempo:** o uso de assistente de IA reduz o tempo necessário para resolver uma
  tarefa de programação?
- **RQ2 — Defeitos:** o uso de assistente de IA reduz a quantidade de defeitos (testes
  de aceitação que falham) no código produzido?
- **RQ3 — Estrutura:** o uso de assistente de IA altera a complexidade ciclomática, a
  duplicação ou o tamanho do código produzido?

### 1.2 Métricas escolhidas

| RQ | Métrica primária | Métricas complementares | Justificativa |
|---|---|---|---|
| RQ1 | Tempo até todos os testes passarem (*time-to-green*), em minutos | — | É o que se quer dizer por "resolver" a tarefa. Trials que não chegam ao verde são **censurados em 35 min** e continuam na análise, porque descartá-los favoreceria o tratamento com mais insucessos. |
| RQ2 | Nº de testes de aceitação falhando ao fim do trial | Taxa de sucesso (testes passando / total) | A contagem absoluta é comparável entre katas porque todas têm oito testes. A taxa deixa o resultado legível. |
| RQ3 | Complexidade ciclomática média por função (Radon `cc`) e % de linhas duplicadas (jscpd) | SLOC (**controle obrigatório**), complexidade por KLOC, Índice de Manutenibilidade (Radon `mi`) | Radon e jscpd são os equivalentes de CK e PMD CPD para Python. O SLOC acompanha as demais métricas porque código mais longo acumula mais complexidade sem ser, por função, mais complexo. |

Dado o N pequeno (quatro trials por integrante), as tabelas descritivas usam **mediana e
IQR** em vez de média e desvio-padrão.

---

## 2. Hipóteses

As hipóteses comparam o tratamento `com_ia` (Copilot ativo) ao tratamento `sem_ia`
(extensão desativada). Todas são avaliadas com o **teste de Wilcoxon signed-rank
pareado**, bilateral, com **α = 0,05**. Ele é não paramétrico e adequado ao desenho
within-subject e à amostra pequena, sem supor normalidade dos tempos, que costumam ter
cauda longa à direita.

A unidade de pareamento é o **integrante**. Cada um resolve cada kata uma única vez, em
um único tratamento, então o par comparado é a mediana dos trials com IA contra a
mediana dos trials sem IA da mesma pessoa. Assim, a diferença de habilidade entre
integrantes sai da comparação.

| RQ | Hipótese nula (H0) | Hipótese alternativa (H1) | Variável dependente |
|---|---|---|---|
| RQ1 | A distribuição do tempo até passar em todos os testes é igual entre os tratamentos. | O tempo até passar em todos os testes é **menor** com IA. | `tempo_ate_verde_min` |
| RQ2 | A distribuição do número de testes falhando ao fim do trial é igual entre os tratamentos. | O número de testes falhando é **menor** com IA. | `testes_falhando` e `taxa_sucesso` |
| RQ3 | As distribuições de complexidade, duplicação e LOC são iguais entre os tratamentos. | Pelo menos uma dessas métricas **difere** entre os tratamentos. | `cc_media`, `cc_total_por_kloc`, `dup_percentual`, `sloc` |

H1 é direcional em RQ1 e RQ2, porque a expectativa corrente é de que o assistente
acelere a resolução e reduza erros, e bilateral em RQ3, porque não há expectativa
firme de direção. O assistente pode tanto simplificar o código, sugerindo construções
idiomáticas, quanto inflá-lo, sugerindo trechos verbosos ou repetidos. Para manter o
critério uniforme, a decisão de rejeitar H0 usa sempre o p-valor bilateral. Nas RQ1 e
RQ2, o p unilateral é reportado como complemento.

Além do p-valor, cada teste reporta o **tamanho de efeito** (correlação rank-biserial
pareada, *r* ∈ [−1, 1]). Com poucos pares, um efeito relevante pode não atingir
significância, e um p-valor isolado não diz quão grande é a diferença.

### 2.1 Variáveis

| Papel | Variável | Níveis / unidade |
|---|---|---|
| Independente (fator) | Tratamento | `com_ia`, `sem_ia` |
| Independente controlada | Kata | `fila-prioridade`, `janela-cobranca`, `agenda-recorrente`, `roteador-notificacoes` |
| Dependente (RQ1) | Tempo até o verde | minutos (censura em 35) |
| Dependente (RQ2) | Testes falhando; taxa de sucesso | contagem; proporção |
| Dependente (RQ3) | Complexidade, duplicação, LOC, MI | CC por função; % de linhas; SLOC; índice 0–100 |
| Controle | Ambiente | Python, pytest, VS Code, Copilot, Radon e jscpd com versões fixadas ([`docs/ambiente.md`](ambiente.md)) |

---

## 3. Metodologia

> _A preencher: ambiente e versões, katas, assistente de IA e versão, sequências de
> contrabalanceamento, procedimento por trial e coleta de métricas. Base:
> [`docs/desenho_experimento.md`](desenho_experimento.md), [`docs/katas.md`](katas.md),
> [`docs/ambiente.md`](ambiente.md), [`docs/formato_log.md`](formato_log.md) e
> [`docs/metricas_estaticas.md`](metricas_estaticas.md)._

---

## 4. Resultados

> _A preencher. Base: [`docs/analise_rq1_rq2.md`](analise_rq1_rq2.md) e
> [`docs/analise_rq3.md`](analise_rq3.md), gerados por `src/analise_rq1_rq2.py` e
> `src/analise_rq3.py`._

### 4.1 RQ1 — Tempo

### 4.2 RQ2 — Defeitos

### 4.3 RQ3 — Estrutura do código

---

## 5. Discussão

> _A preencher: interpretação dos resultados, ameaças à validade observadas na execução e
> limitações._

---

## 6. Conclusão

> _A preencher._
