# LAB05 - DuckDB x SQLite
# Alvos marcados com TODO são implementados pelo Integrante B (tarefas B-1.x).
PYTHON ?= python
PHASE  ?= pilot

.PHONY: help test preflight data pilot run validate analyze dashboard

help:
	@echo "Alvos: test | preflight | data | pilot | run | validate | analyze PHASE=pilot|full | dashboard"

test:
	$(PYTHON) -m pytest

preflight:
	$(PYTHON) -c "import yaml; from bench.run_matrix import preflight; preflight(yaml.safe_load(open('bench/config.yaml', encoding='utf-8'))) "

data:
	$(PYTHON) -c "from pathlib import Path; from bench.datagen import generate; [generate(sf, Path('data/db')) for sf in (0.1, 1)]"

pilot:
	$(MAKE) preflight
	$(PYTHON) -c "from bench.env_snapshot import snapshot; snapshot()"
	$(PYTHON) -m bench.run_matrix --phase pilot --resume
	$(MAKE) validate
	$(PYTHON) -c "from pathlib import Path; from analysis.lab05.manifest import write_manifest; write_manifest([p for p in (Path('data/db')).glob('*') if p.is_file()], Path('data/manifest.json'))"

run:
	$(PYTHON) -m bench.run_matrix --phase full --resume

validate:
	$(PYTHON) -c "import yaml,pandas as pd; from analysis.lab05.validate import validate; cfg=yaml.safe_load(open('bench/config.yaml',encoding='utf-8')); df=pd.read_csv('data/processed/results.csv') if __import__('pathlib').Path('data/processed/results.csv').exists() else pd.DataFrame(); problems=validate(df,cfg,'pilot' if 'pilot' in '$(PHASE)' else 'full'); print('\n'.join(problems)); raise SystemExit(1 if any(p.startswith('PROBLEMA') for p in problems) else 0)"

analyze:
	@echo "TODO (A-2.3): python -m analysis.lab05.report --phase $(PHASE)"

dashboard:
	@echo "TODO (B-3.2): streamlit run analysis/dashboard/app.py"
