# Catálogo e validação das katas

O catálogo contém quatro tarefas autorais, curtas e independentes. Elas usam a
mesma convenção: uma função pura em Python, sem rede, relógio, arquivos ou
dependências externas. Cada kata tem oito testes de aceitação, incluindo casos
de borda, e deve ser resolvível dentro do time-box de 35 minutos.

## Critérios de seleção

Uma kata só entra no experimento se:

1. tiver enunciado e identificador estáveis;
2. tiver pelo menos seis testes de aceitação coletáveis pelo pytest;
3. for determinística e executável offline;
4. não exigir conhecimento de framework ou biblioteca específica;
5. tiver esforço estimado entre 20 e 30 minutos para um participante familiarizado
   com Python;
6. não for uma variação direta de FizzBuzz, Calculadora de Strings, Fibonacci,
   Kata de Bowling ou outro exercício clássico facilmente memorizável;
7. tiver interface e volume de testes comparáveis às demais tarefas.

## Tarefas selecionadas

| ID | Tarefa | O que exercita | Por que tem baixa memorização |
|---|---|---|---|
| `fila-prioridade` | Ordena pedidos por urgência, prazo e ordem de chegada, preservando desempates. | Chave de ordenação composta e regras de desempate. | Domínio autoral de pedidos; não é uma kata clássica com solução canônica. |
| `janela-cobranca` | Agrupa eventos de cobrança em janelas de tamanho fixo e soma valores por janela. | Intervalos, fronteiras e agregação. | Enunciado de domínio específico, sem implementação pronta esperada. |
| `agenda-recorrente` | Expande compromissos recorrentes até uma data final, sem incluir ocorrências fora do intervalo. | Datas, limites inclusivos e geração de sequência. | Combina regras de recorrência autorais e não depende de framework. |
| `roteador-notificacoes` | Escolhe o canal disponível de notificação por prioridade e aplica fallback. | Validação de dados, prioridade e fallback determinístico. | Cenário específico de canais e política de fallback criada para o experimento. |

Os esqueletos e testes ficam em `katas/<id>/`. O arquivo `kata.py` não contém a
solução: ele lança `NotImplementedError` para impedir que o código de referência
seja confundido com o código produzido nos trials. O validador roda apenas a
coleta dos testes, portanto a falha esperada da implementação não impede a
preparação da S01.

## Validação antes da S02

Na raiz de `Laboratorio02`, execute:

```powershell
python src\valida_katas.py
```

O comando verifica o manifesto, os identificadores, a presença dos esqueletos,
a quantidade de testes e a coleta com pytest. Ele deve terminar com `4 kata(s)
validada(s).` Antes de congelar o catálogo, o trio também deve revisar os
enunciados e confirmar que nenhum participante já conhece uma solução específica.
