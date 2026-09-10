# Coleta das métricas estáticas (RQ03)

Define como as métricas estruturais do código de cada trial são coletadas na
execução do experimento (Lab02S02). Os dados são produzidos pelo script
[`src/metricas_estaticas.py`](../src/metricas_estaticas.py) e exportados para
`data/metricas.csv` e `data/metricas.json`.

As ferramentas e suas versões estão fixadas em
[`docs/ambiente.md`](ambiente.md): **Radon** (complexidade ciclomática, LOC e
Índice de Manutenibilidade) e **jscpd** (duplicação). O enunciado indica CK e
PMD CPD, que só medem Java; como a linguagem fixada é Python, usamos os
equivalentes previstos no próprio enunciado.

## Onde fica o código de cada trial

Por convenção, o código final de um trial fica em:

```
Laboratorio02/trials/<trial_id>/
```

O `<trial_id>` é **o mesmo** gerado pelo cronômetro e registrado em
`data/trials.csv` (ver [`docs/formato_log.md`](formato_log.md)). É essa chave que
permite juntar, na análise da S03, o tempo e a taxa de sucesso de um trial com as
suas métricas estruturais — sem redigitar integrante, kata ou tratamento em
nenhum lugar.

Ao terminar um trial, o integrante copia o código para essa pasta e commita
referenciando a Issue do trial.

## Como rodar

Um trial específico:

```bash
python src/metricas_estaticas.py --trial-id <trial_id>
```

Todos os trials já registrados em `data/trials.csv` (uso normal ao final de uma
rodada de trials):

```bash
python src/metricas_estaticas.py --todos
```

Código fora da pasta padrão:

```bash
python src/metricas_estaticas.py --trial-id <trial_id> --codigo-dir <caminho>
```

Rodar de novo o mesmo `trial_id` **substitui** a linha anterior, não acumula
linhas duplicadas. Trials sem pasta de código são apenas listados no final e
nada é gravado para eles.

Flags úteis:

| Flag | Efeito |
|---|---|
| `--nao-registrar` | Só imprime as métricas, sem gravar no CSV. |
| `--excluir` | Padrões de arquivo excluídos da medição (default: `test_*.py,*_test.py,conftest.py`). |
| `--min-lines`, `--min-tokens` | Tamanho mínimo de um clone para o jscpd (default: 5 linhas / 50 tokens). |
| `--integrante`, `--kata`, `--tratamento` | Preenchem esses campos quando o trial ainda não está em `data/trials.csv`. |
| `--observacoes` | Observação livre gravada na linha. |

## O que é e o que não é medido

- **Medido:** os arquivos `.py` que o integrante escreveu durante o trial.
- **Não medido:** os testes de aceitação da kata (`test_*.py`, `*_test.py`,
  `conftest.py`) e os diretórios `tests/`, `.venv/`, `__pycache__/`,
  `.pytest_cache/`, `node_modules/`, `.git/`.

Os testes são excluídos de propósito: eles vêm prontos com a kata, são
**idênticos** nos trials `com_ia` e `sem_ia`, e incluí-los diluiria as métricas
do código que é justamente o objeto da comparação — quanto maior o peso do
código comum aos dois tratamentos, menor a diferença observável entre eles.

A lista de arquivos é calculada pelo script e passada explicitamente às duas
ferramentas, em vez de deixar cada uma aplicar seus próprios filtros. Se o Radon
e o jscpd analisassem conjuntos diferentes, o percentual de duplicação e o LOC
que o normaliza teriam bases distintas. A coluna `arquivos` registra exatamente
o que entrou na medição.

## Schema do CSV/JSON (`data/metricas.csv`, `data/metricas.json`)

| Coluna | Tipo | Descrição |
|---|---|---|
| `trial_id` | string | Chave do trial, a mesma de `data/trials.csv`. |
| `integrante` | string | Lido de `data/trials.csv` pelo `trial_id`. |
| `kata` | string | Lido de `data/trials.csv` pelo `trial_id`. |
| `tratamento` | `com_ia` \| `sem_ia` | Lido de `data/trials.csv` pelo `trial_id`. |
| `codigo_dir` | string | Diretório do código medido, relativo a `Laboratorio02/`. |
| `arquivos_analisados` | int | Quantidade de arquivos que entraram na medição. |
| `arquivos` | string | Nomes desses arquivos, separados por `;`. |
| `loc` | int | Linhas totais (Radon `raw`: `loc`). |
| `sloc` | int | Linhas de código sem comentários nem linhas em branco (Radon `raw`: `sloc`). **Métrica de controle.** |
| `linhas_comentario` | int | Linhas de comentário (`single_comments` + `multi`). |
| `linhas_branco` | int | Linhas em branco. |
| `funcoes` | int | Nº de funções/métodos considerados no cálculo da complexidade. |
| `cc_media` | float | **Complexidade ciclomática média (McCabe) por função/método** — métrica primária da RQ03. |
| `cc_mediana` | float | Mediana das complexidades (preferida na agregação entre trials, dado o N pequeno). |
| `cc_max` | int | Maior complexidade encontrada — indica o "pior" ponto do código. |
| `cc_total` | int | Soma das complexidades. |
| `cc_total_por_kloc` | float | `cc_total` normalizado por KLOC (`cc_total / (sloc/1000)`). |
| `mi_medio` | float | Índice de Manutenibilidade médio entre os arquivos (Radon `mi`). Métrica opcional. |
| `dup_percentual` | float | **% de linhas duplicadas** (jscpd: `statistics.total.percentage`). |
| `dup_linhas` | int | Nº absoluto de linhas duplicadas. |
| `dup_clones` | int | Nº de blocos clonados detectados. |
| `radon_versao` | string | Versão do Radon usada na coleta. |
| `jscpd_versao` | string | Versão do jscpd usada na coleta. |
| `jscpd_min_lines` | int | Mínimo de linhas de um clone nesta coleta. |
| `jscpd_min_tokens` | int | Mínimo de tokens de um clone nesta coleta. |
| `timestamp_coleta` | ISO-8601 (UTC) | Quando a coleta foi executada. |
| `observacoes` | string | Observações e avisos (ex.: duplicação não coletada, diretório sem arquivos elegíveis). |

### Por que LOC é obrigatório junto de complexidade e duplicação

O enunciado exige LOC como métrica de controle, e o motivo aparece direto nos
dados: código gerado com assistente tende a ser mais verboso. Um `cc_total`
maior pode ser apenas efeito de haver mais código, não de o código ser mais
complexo. Por isso a RQ03 é lida com três colunas juntas — `cc_media` (por
função), `cc_total_por_kloc` (normalizada por tamanho) e `sloc` (o tamanho em si)
— e nunca com o total absoluto isolado.

### Como o Radon é lido

Duas particularidades do formato do `radon cc -j` são tratadas pelo script, e
ambas afetariam o número final:

1. **Entradas de classe são agregados.** Os métodos de uma classe aparecem
   dentro da entrada da classe **e também** repetidos no nível de cima da lista.
   Contar a classe junto dos métodos inflaria `funcoes` e `cc_total`; por isso a
   entrada de tipo `class` é ignorada.
2. **Funções internas (closures) não são repetidas no nível de cima.** Elas só
   existem aninhadas no campo `closures`, então o script desce nesse campo — sem
   isso, funções aninhadas ficariam fora da média.

O resultado é exatamente o que a RQ03 pede: uma complexidade por função ou
método efetivamente escrito.

## Métrica não coletada nunca vira zero

Se uma ferramenta não estiver instalada ou falhar, a coluna correspondente fica
**vazia** e o motivo é registrado em `observacoes` — nunca é preenchida com `0`.
Um zero seria lido na análise como "código sem complexidade" ou "código sem
duplicação", o que enviesaria a comparação entre os tratamentos.

O script exige o Radon para rodar (aponta o `verifica_ambiente.py` se ele
faltar). Já a ausência do jscpd não interrompe a coleta: as métricas de
complexidade e LOC são gravadas e só a duplicação fica pendente, com o aviso
correspondente.
