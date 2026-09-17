# Formato padrão de log dos trials

Define o formato usado para registrar os trials naexecução do experimento(Lab02S02).
 Os dados são coletados pelo script [`src/cronometro_trial.py`](../src/cronometro_trial.py)
  e exportados para`data/trials.csv` e `data/trials.json`.

## Como rodar um trial

Antes de iniciar o cronômetro, copie o esqueleto da kata (de `katas/<id>/`,
ver [`docs/katas.md`](katas.md)) para uma pasta de trabalho — é nela que o
código é editado durante o trial:

```powershell
Copy-Item -Recurse katas\<id-do-kata> trials\_work\<id-do-kata>_<tratamento>
```

Depois, rode o cronômetro apontando `--test-cmd` e `--codigo-dir` para essa
pasta:

```bash
python src/cronometro_trial.py \
  --integrante "<nome>" \
  --kata "<id-do-kata>" \
  --tratamento com_ia \
  --test-cmd "pytest trials/_work/<id-do-kata>_<tratamento>" \
  --codigo-dir "trials/_work/<id-do-kata>_<tratamento>"
```

Fluxo:
1. O script inicia o cronômetro e imprime as instruções.
2. Pressione **ENTER** a qualquer momento para encerrar o trial manualmente
   (ex.: terminou de resolver o kata).
3. Se ninguém pressionar ENTER, o trial é encerrado automaticamente ao
   atingir o **time-box de 35 min** e marcado como **censurado** — o tempo é
   registrado como exatamente 35 min, e o trial **não é descartado**.
4. Ao encerrar (manual ou censura), o script roda `--test-cmd` automaticamente
   e classifica o resultado (ver `status` abaixo).
5. Se `--codigo-dir` foi informado, o script copia essa pasta para
   `trials/<trial_id>/` automaticamente — é lá que
   [`src/metricas_estaticas.py`](../src/metricas_estaticas.py) procura o
   código do trial na S03. Sem `--codigo-dir`, essa cópia precisa ser feita à
   mão antes de rodar as métricas.

O time-box só pode ser **reduzido** via `--timebox <min>`, nunca aumentado
(`--timebox` > 35 é rejeitado pelo script), conforme o enunciado.

## Schema do CSV/JSON (`data/trials.csv`, `data/trials.json`)

| Coluna | Tipo | Descrição |
|---|---|---|
| `trial_id` | string | Identificador único do trial. Default: `<integrante>_<kata>_<tratamento>_<timestamp>`. |
| `integrante` | string | Nome de quem executou o trial. |
| `kata` | string | Identificador/nome do kata resolvido. |
| `tratamento` | `com_ia` \| `sem_ia` | Tratamento aplicado ao trial. |
| `timestamp_inicio` | ISO-8601 (UTC) | Início do cronômetro. |
| `timestamp_fim` | ISO-8601 (UTC) | Fim do trial (parada manual ou censura). |
| `tempo_segundos` | float | Tempo até parar/censurar, em segundos. |
| `tempo_minutos` | float | Mesmo valor, em minutos (conveniência). |
| `timebox_minutos` | float | Time-box efetivamente usado no trial (≤ 35). |
| `status` | `passou` \| `falhou` \| `censurado` | Ver regras abaixo. |
| `testes_passando` | int \| vazio | Nº de testes que passaram, extraído da saída de `--test-cmd`. |
| `testes_total` | int \| vazio | Nº total de testes, extraído da saída de `--test-cmd`. |
| `exit_code` | int | Código de saída do comando de teste. |
| `test_cmd` | string | Comando de teste executado (para reprodutibilidade). |
| `log_path` | string | Caminho relativo do log bruto da execução dos testes (`data/logs/<trial_id>.log`). |
| `observacoes` | string | Observações livres (`--observacoes`). |

### Regras de `status`

- **`passou`** — trial encerrado manualmente antes do time-box e `exit_code == 0` (todos os testes de aceitação passando).
- **`falhou`** — trial encerrado manualmente antes do time-box, mas `exit_code != 0` (nem todos os testes passando).
- **`censurado`** — o time-box foi atingido antes de uma parada manual. `tempo_minutos` é fixado no valor do time-box (ex.: 35 min). **O trial permanece no dataset** (nunca é descartado) — é assim que o RQ1 deve tratar tentativas sem sucesso, conforme o enunciado.

### Extração de `testes_passando`/`testes_total`

O parser reconhece automaticamente a saída de `pytest`, `jest`, `unittest` e
Maven/JUnit (`Tests run: N, Failures: F, Errors: E`). Se o runner usado não
for reconhecido, essas duas colunas ficam vazias e apenas `status`/`exit_code`
são usados — nesse caso, é possível informar os valores manualmente com
`--passed` e `--total` como fallback.

O log bruto completo (stdout+stderr) do comando de teste fica salvo em
`data/logs/<trial_id>.log`, independentemente do parser ter reconhecido o
formato ou não — útil para auditoria e para o Integrante B relacionar o
trial ao código final analisado por CK/PMD na S02/S03.

## Convenção de `tratamento` e `kata`

- `tratamento` usa sempre os valores `com_ia` ou `sem_ia` (snake_case, sem
  acento) — é o mesmo texto usado nas análises estatísticas do Passo 4.
- `kata` deve usar o mesmo identificador definido pelo Integrante C na lista
  de katas (Passo 2), para permitir agregações por kata entre os três
  integrantes.

## Exemplo de trial

```bash
python src/cronometro_trial.py \
  --integrante "Ana" \
  --kata "string-calculator" \
  --tratamento com_ia \
  --test-cmd "pytest -q"
```

Gera uma linha como:

```
trial_id=Ana_string-calculator_com_ia_20260910T143201, status=passou,
tempo_minutos=12.4, testes_passando=8, testes_total=8
```
