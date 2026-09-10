# Ambiente do experimento

Define o ambiente único em que os três integrantes executam os trials do Lab02 e
como cada máquina é conferida antes da execução. O ambiente é verificado e
registrado pelo script [`src/verifica_ambiente.py`](../src/verifica_ambiente.py),
que exporta o snapshot para `data/ambiente.csv` e `data/ambiente.json`.

O objetivo é que a **única** diferença entre um trial `com_ia` e um trial
`sem_ia` seja o assistente de IA. Linguagem, IDE, runner de testes e
ferramentas de métrica são os mesmos em todos os trials do grupo.

## Decisões fixadas

| Item | Decisão | Por quê |
|---|---|---|
| Linguagem das katas | **Python 3.10+** | O CK só mede Java; o enunciado permite ferramenta equivalente, e o Radon cobre complexidade, LOC e manutenibilidade em Python. O grupo já usou Python no Lab01, o que reduz o efeito de familiaridade com a linguagem sobre o tempo medido. |
| Runner de testes | **pytest** | É o runner cujo formato de saída o [cronômetro](../src/cronometro_trial.py) já reconhece para extrair `testes_passando`/`testes_total`. |
| IDE | **Visual Studio Code** | Único IDE comum aos três, e é onde o assistente de IA escolhido roda como extensão — o que permite ligar e desligar o tratamento sem trocar de ferramenta. |
| Assistente de IA | **GitHub Copilot** (extensão `github.copilot`) | O enunciado exige o mesmo assistente em todos os trials e sugere o Copilot gratuito via GitHub Student Developer Pack. Sendo extensão do IDE, o tratamento é ligado/desligado de forma verificável (ver protocolo abaixo), diferente de um chatbot em aba do navegador. |
| Complexidade ciclomática, LOC e MI | **Radon** (`cc`, `raw`, `mi`) | Equivalente ao CK para Python. `raw` fornece o LOC exigido como métrica de controle. |
| Duplicação de código | **jscpd** | O Radon não mede duplicação; o enunciado indica o jscpd como equivalente ao PMD CPD fora do Java. |
| Time-box | **35 min por trial** | Valor do enunciado. O script de cronometragem recusa `--timebox` maior que 35. |

Cada integrante executa **todos os seus trials na mesma máquina**, com o mesmo
ambiente. O desenho é within-subject: o par (com_ia, sem_ia) de um integrante só
é comparável se o ambiente não mudar entre os dois trials.

## Preparação da máquina

No PowerShell, a partir da raiz do repositório:

```powershell
cd Laboratorio02
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r src\requirements.txt
```

A duplicação é medida por uma ferramenta Node.js, instalada globalmente (fora do
venv):

```powershell
npm install -g jscpd
```

O assistente de IA é instalado como extensão do VS Code:

```powershell
code --install-extension github.copilot
```

## Conferência do ambiente

Com o venv ativo, cada integrante roda uma vez, antes do primeiro trial:

```powershell
python src\verifica_ambiente.py --integrante "<nome>"
```

O script confere os nove itens da tabela acima, imprime um relatório com as
versões encontradas e **grava o snapshot** em `data/ambiente.csv` (uma linha por
integrante — rodar de novo substitui a linha anterior, não acumula). Ele termina
com código de saída `1` enquanto faltar qualquer item obrigatório, e `0` quando o
ambiente está pronto.

Para apenas conferir, sem gravar: `--nao-registrar`.

O script inspeciona somente as extensões do assistente escolhido
(`github.copilot`, `github.copilot-chat`) — as demais extensões instaladas na
máquina não fazem parte do desenho do experimento e não são registradas.

### Schema de `data/ambiente.csv` / `data/ambiente.json`

| Coluna | Descrição |
|---|---|
| `integrante` | Nome de quem executou a verificação. |
| `timestamp_verificacao` | Data/hora ISO-8601 (UTC) da verificação. |
| `sistema_operacional` | Sistema e release da máquina usada nos trials. |
| `python_versao` | Versão do interpretador que roda as katas e os testes. |
| `pytest_versao` | Versão do runner dos testes de aceitação. |
| `radon_versao` | Versão da ferramenta de complexidade/LOC/MI. |
| `node_versao` | Versão do runtime exigido pelo jscpd. |
| `jscpd_versao` | Versão da ferramenta de duplicação. |
| `ide_versao` | Versão do VS Code. |
| `assistente_ia` | Nome do assistente fixado para o grupo. |
| `assistente_ia_versao` | Versão da extensão do assistente — é o dado que o Relatório Final precisa citar para permitir replicação. |
| `git_versao` | Versão do git usada para versionar o código dos trials. |
| `itens_faltando` | Lista dos itens obrigatórios ausentes (vazio quando o ambiente está pronto). |
| `pronto` | `True` se nenhum item obrigatório falta. |

## Protocolo dos tratamentos

O tratamento precisa ser ligado/desligado do mesmo jeito por todos, senão a
variável independente fica mal definida.

**Trial `com_ia`:**

1. Abrir a pasta do kata no VS Code com o Copilot **ativo**.
2. Uso livre de sugestões inline e do chat da extensão.
3. Opcionalmente, anotar o número de prompts em `--observacoes` do cronômetro
   (métrica exploratória da RQ01).

**Trial `sem_ia`:**

1. Abrir a pasta do kata com a extensão **desabilitada na sessão**:

   ```powershell
   code --disable-extension github.copilot <pasta-do-kata>
   ```

   Desabilitar por sessão é preferível a desinstalar: não altera o ambiente
   registrado no snapshot e evita reinstalar a extensão entre trials.
2. Nenhuma consulta a chatbot, tradutor de código ou ferramenta de geração em
   aba do navegador.
3. Consulta à **documentação oficial da linguagem/biblioteca é permitida** nos
   dois tratamentos — é o que um dev faz normalmente, e proibir só em um dos
   lados criaria uma segunda diferença entre os tratamentos.

Em ambos os casos, o trial é iniciado pelo cronômetro
([`docs/formato_log.md`](formato_log.md)) e o código final é preservado para a
coleta das métricas estáticas
([`docs/metricas_estaticas.md`](metricas_estaticas.md)).

## Limitações do ambiente registradas

- **A versão do assistente pode mudar durante o experimento.** A extensão se
  atualiza sozinha. O snapshot é tirado antes dos trials e a versão fica
  registrada; se houver atualização no meio da execução, o integrante roda o
  script de novo e a mudança fica visível no histórico do `data/ambiente.csv`.
- **Máquinas diferentes entre integrantes.** O snapshot registra SO e versões de
  cada um. Como a comparação é within-subject (cada integrante é seu próprio
  controle), diferença de máquina entre integrantes não invalida o pareamento,
  mas fica documentada para a discussão de validade externa.
- **O Copilot exige licença ativa** (Student Developer Pack). Sem licença, a
  extensão instala mas não sugere, e o trial `com_ia` viraria um `sem_ia`
  disfarçado — por isso o primeiro trial `com_ia` de cada integrante só começa
  depois de confirmar que as sugestões estão aparecendo.
