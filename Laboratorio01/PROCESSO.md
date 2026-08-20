# Configuração do processo — Kanban do grupo

Documento de referência do fluxo de trabalho do grupo no GitHub Projects (v2).
Vale para o Lab01 e para os laboratórios seguintes do semestre.

- **Repositório:** https://github.com/gabrieltinoco/Laboratorio-Experimentacao-de-Software
- **GitHub Projects (v2):** https://github.com/users/gabrieltinoco/projects/2
- **Integrantes:** Arthur Miranda Pacher (`art1544`), Gabriel Lage Silva (`gabitolage`), Gabriel Lucas Tinoco de Aguiar (`gabrieltinoco`)

## Colunas do board (campo Status)

O fluxo é `Backlog → To do → Doing → Review → Done`. Cada coluna tem critério
explícito de entrada e de saída, para que a posição do cartão signifique sempre a
mesma coisa para os três integrantes.

| Coluna | Entra quando | Sai quando |
|---|---|---|
| **Backlog** | A tarefa foi identificada e virou Issue, mas ainda não foi comprometida com nenhuma sprint | O grupo aceita a tarefa para a sprint atual e define o Assignee |
| **To do** | A tarefa está comprometida com a sprint corrente e tem responsável definido | O responsável começa efetivamente a trabalhar nela |
| **Doing** | Existe trabalho em andamento agora — código sendo escrito, dados sendo validados, texto sendo redigido | O trabalho está concluído e commitado, referenciando o número da Issue |
| **Review** | O resultado está no repositório e pode ser conferido pelos outros integrantes | O resultado foi conferido e atende ao que a Issue pedia |
| **Done** | A Issue foi cumprida e conferida | Nunca (estado final da sprint) |

Todo cartão é uma Issue de verdade do repositório, com Assignee definido. Não são
usadas *draft issues*.

## Limite de WIP

**Doing: no máximo 2 cartões por integrante — 6 no board como um todo, com o trio
completo.**

Justificativa:

1. **A divisão de trabalho do laboratório é de duas frentes por pessoa.** As RQs
   foram distribuídas em três partes, e cada integrante ficou com duas RQs por
   sprint (RQ01+RQ02, RQ03+RQ04, RQ05+RQ06+RQ07). Um limite de 2 permite que o
   integrante trabalhe nas suas duas frentes sem precisar serializar
   artificialmente uma atrás da outra, e ao mesmo tempo o impede de abrir uma
   terceira frente antes de fechar as duas que já pegou.
2. **O ciclo de trabalho é semanal.** Entre uma aula e a outra há uma janela
   curta. Mais de 2 cartões simultâneos por pessoa nessa janela produz cartão
   parado em Doing de uma semana para a outra, que é exatamente o "cartão
   fantasma" penalizado na avaliação do board.
3. **Alinhado à sugestão da disciplina.** As regras da disciplina sugerem 2
   cartões por pessoa ativa no board; mantemos esse número em vez de inventar
   outro, para não ter de justificar desvio.

O limite é por integrante, e não um número único para a coluna, porque o board é
compartilhado por três pessoas trabalhando em paralelo: um teto global de 2 faria
dois integrantes ficarem bloqueados enquanto o terceiro trabalha.

**Review não tem limite numérico**, mas tem regra: nenhuma sprint fecha com
cartão em Review. Se algo chega ao fim da sprint sem revisão, ele volta para
Doing e é reportado como impedimento na daily.

## Rotina de snapshot

O GitHub Projects v2 não mantém histórico consultável de mudança de coluna, então
o estado do board é exportado por script próprio para CSV e acumulado ao longo do
semestre. Essa série é a base de dados dos Labs 04 e 05 e a evidência objetiva da
evolução semanal.

```bash
cd Laboratorio01
python src/export_project_snapshot.py --sprint Lab01S02
```

Regras da rotina:

- **Uma execução por sprint**, no fechamento da sprint, com o board já
  atualizado — nunca no meio do caminho, senão o snapshot registra cartões em
  `To do` que já foram entregues.
- **O CSV nunca é editado à mão.** A coluna `sprint` identifica a execução que
  capturou aquele estado, não a sprint a que o cartão pertence. Se um snapshot
  saiu errado, a correção é reexportar, não editar. O script recusa gravar uma
  sprint que já existe no arquivo justamente para forçar isso.
- O identificador segue o padrão do enunciado: `Lab01S01`, `Lab01S02`,
  `Lab01S03`, e assim por diante nos próximos laboratórios.

## Convenção de commits

Todo commit referencia o número da Issue correspondente, no início da mensagem:

```
#7 #8 valida consistencia das RQ03 e RQ04 nos 1000 repositorios
```

Commit sem referência a Issue não é considerado na correção, mesmo estando no
repositório.
