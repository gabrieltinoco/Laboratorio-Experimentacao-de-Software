# Desenho do experimento

O experimento compara a resolução das mesmas tarefas com o GitHub Copilot ativo e
desativado, mantendo linguagem, IDE, testes, time-box e ambiente fixos. O
catálogo das tarefas está em [`data/katas.csv`](../data/katas.csv) e a
validação estrutural é feita por [`src/valida_katas.py`](../src/valida_katas.py).

## Objetivo e questões de pesquisa

O objetivo é comparar, em tarefas de programação de dificuldade semelhante, o
efeito do assistente de IA sobre tempo de resolução, defeitos funcionais e
estrutura do código produzido.

- **RQ1:** o uso do assistente reduz o tempo até todos os testes passarem?
- **RQ2:** o uso do assistente reduz a quantidade de testes que falham ao fim do
  time-box?
- **RQ3:** o uso do assistente altera complexidade ciclomática, duplicação ou
  LOC do código produzido?

## Hipóteses

As hipóteses são formuladas para o tratamento `com_ia` comparado ao tratamento
`sem_ia`. O teste inferencial planejado é Wilcoxon pareado, bilateral, com
`alpha = 0,05`, por causa do desenho within-subject e do tamanho amostral
pequeno.

| Questão | Hipótese nula (H0) | Hipótese alternativa (H1) |
|---|---|---|
| RQ1 | A distribuição do tempo até passar em todos os testes é igual entre os tratamentos. | O tempo até passar em todos os testes é menor com IA. |
| RQ2 | A distribuição do número de testes falhando ao fim do trial é igual entre os tratamentos. | O número de testes falhando é menor com IA. |
| RQ3 | As distribuições de complexidade, duplicação e LOC são iguais entre os tratamentos. | Pelo menos uma dessas métricas difere entre os tratamentos. |

Para RQ1, trials que não terminarem com sucesso permanecem na análise como
observações censuradas em 35 minutos. Para RQ2, usa-se a contagem de testes
falhando (`testes_total - testes_passando`) e também a taxa de sucesso. Para
RQ3, a análise sempre reporta LOC junto com complexidade e duplicação.

## Variáveis e unidades de análise

| Papel | Variável | Operacionalização |
|---|---|---|
| Independente | Tratamento | `com_ia` ou `sem_ia`; no primeiro, Copilot ativo; no segundo, extensão desativada na sessão. |
| Independente controlada | Kata | Uma das quatro tarefas do catálogo, identificada por `kata`. |
| Dependente primária | Tempo | Minutos até todos os testes passarem; 35 min para trial censurado. |
| Dependente | Defeitos | Número de testes de aceitação falhando ao final do time-box e taxa de testes passando. |
| Dependente | Estrutura | Complexidade ciclomática média/mediana, LOC, SLOC, MI e percentual de duplicação. |
| Exploratório | Interações | Número de prompts/interações com o assistente, anotado no log quando possível. |
| Controle | Ambiente | Python, pytest, Radon, jscpd, VS Code, Copilot e SO registrados pelo snapshot de ambiente. |

Cada observação é um trial `(integrante, kata, tratamento)`. A unidade
estatística principal é o par de trials do mesmo integrante e kata, um em cada
tratamento. A mediana e o IQR serão priorizados nas tabelas descritivas.

## Projeto experimental

O desenho é **crossover within-subject contrabalanceado**. Cada integrante
resolve as quatro katas, duas com IA e duas sem IA, sob time-box de 35 minutos
por trial. O tratamento é alternado por kata para evitar que toda a ordem de
aprendizado fique concentrada em um único tratamento.

Com quatro katas, usar as sequências abaixo, distribuídas entre os integrantes:

| Sequência | Kata 1 | Kata 2 | Kata 3 | Kata 4 |
|---|---|---|---|---|
| A | `fila-prioridade` com IA | `janela-cobranca` sem IA | `agenda-recorrente` com IA | `roteador-notificacoes` sem IA |
| B | `fila-prioridade` sem IA | `janela-cobranca` com IA | `agenda-recorrente` sem IA | `roteador-notificacoes` com IA |

Cada integrante deve receber uma sequência definida antes de iniciar os trials.
Não se deve trocar o tratamento de uma tarefa depois de iniciado o trial.

### Procedimento por trial

1. Conferir o snapshot do ambiente e abrir somente a pasta da kata.
2. Ativar ou desativar o Copilot conforme o tratamento sorteado.
3. Iniciar `src/cronometro_trial.py` com o identificador da kata.
4. Trabalhar por no máximo 35 minutos e executar os testes de aceitação.
5. Preservar o código final, o log bruto e a linha gerada em `data/trials.csv`.
6. Registrar observações sobre interrupções, prompts e desvios do protocolo.

## Ameaças à validade e mitigação

| Ameaça | Risco | Mitigação e evidência |
|---|---|---|
| Efeito de aprendizado | O segundo trial pode ser mais rápido por prática com o formato. | Contrabalancear a ordem A/B, usar tarefas distintas e registrar a ordem no protocolo. |
| Familiaridade com Copilot | Um integrante pode conhecer melhor a ferramenta. | Registrar experiência prévia no formulário do participante, usar o mesmo assistente/versão e interpretar isso como possível moderador. |
| Vazamento ou memorização da solução | Uma solução vista na primeira condição pode ser reutilizada na segunda. | Katas com enunciados originais, não baseados em exercícios clássicos; não consultar código de outro trial; manter diretórios separados. |
| Diferença de dificuldade entre katas | Uma tarefa mais difícil pode dominar a comparação. | Quatro katas com mesma interface de função, quantidade semelhante de testes e faixa de dificuldade pré-avaliada; pareamento por kata na análise. |
| Viés de seleção dos katas | Tarefas muito indexadas podem medir memória, não assistência. | Catalogar justificativa de baixa indexação e fazer busca exploratória antes de congelar o catálogo. |
| Efeito de ordem e fadiga | Trials posteriores podem sofrer cansaço ou perda de atenção. | Limitar a quatro trials por integrante, fazer pausas padronizadas e registrar horário/ordem. |
| Falha de medição do tempo | Interrupções ou comando de teste incorreto podem distorcer o time-to-green. | Usar o cronômetro comum, salvar stdout/stderr e marcar interrupções em `observacoes`; excluir apenas logs inválidos, com justificativa. |
| Violação do tratamento sem IA | Consultar chatbot ou deixar extensão ativa contamina o controle. | Iniciar o VS Code com `--disable-extension github.copilot`, conferir o ambiente e registrar desvios como protocolo inválido. |
| Variação de ambiente | Máquinas e versões diferentes podem afetar desempenho. | Rodar `verifica_ambiente.py`, manter o ambiente de cada integrante constante e usar within-subject. |
| Reatividade e expectativa | Saber o tratamento pode mudar esforço ou comportamento. | Instruções idênticas, ordem pré-definida e registro objetivo de tempo/testes; reconhecer que cegamento não é possível. |
| Censura em 35 minutos | Muitos insucessos podem esconder diferenças de tempo entre soluções. | Tratar 35 min como censura, reportar taxa de sucesso separadamente e não descartar trials. |
| Baixo poder estatístico | Três integrantes e quatro pares fornecem pouca potência. | Reportar tamanho de efeito, intervalos/estatísticas descritivas e tratar o estudo como experimento exploratório. |

## Critério de congelamento

Antes da execução da S02, o trio deve revisar e congelar `data/katas.csv`, os
testes de aceitação e as sequências A/B. Depois do primeiro trial, alterações em
enunciado ou testes exigem registrar uma nova versão e justificar a quebra de
comparabilidade.
