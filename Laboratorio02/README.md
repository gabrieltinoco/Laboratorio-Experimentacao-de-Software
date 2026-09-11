# LAB02 - Sprint 1

Os artefatos do Integrante C estão organizados assim:

- [`docs/desenho_experimento.md`](docs/desenho_experimento.md): hipóteses,
	variáveis, desenho crossover within-subject e ameaças à validade.
- [`docs/katas.md`](docs/katas.md): critérios de seleção, justificativa e
	protocolo de congelamento das katas.
- [`data/katas.csv`](data/katas.csv): catálogo versionado usado pelos trials.
- `katas/<id>/`: esqueletos e testes de aceitação das quatro tarefas.
- [`src/valida_katas.py`](src/valida_katas.py): validação automática do catálogo
	e da coleta dos testes.

Com o ambiente preparado por [`src/requirements.txt`](src/requirements.txt),
execute na pasta `Laboratorio02`:

```powershell
python src\valida_katas.py
```
