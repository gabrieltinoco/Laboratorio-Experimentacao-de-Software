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
	@echo "TODO (B-1.3/B-1.4): checagem de CPU, RAM e disco"

data:
	@echo "TODO (B-1.1): gerar TPC-H sf 0.1 e 1 nos dois bancos"

pilot:
	@echo "TODO (B-1.4): preflight + snapshot + run_matrix --phase pilot --resume + validate + manifest"

run:
	@echo "TODO (B-1.4/B-2.1): run_matrix --phase full --resume"

validate:
	@echo "TODO (B-1.4): validar data/processed/results.csv"

analyze:
	@echo "TODO (A-2.3): python -m analysis.lab05.report --phase $(PHASE)"

dashboard:
	@echo "TODO (B-3.2): streamlit run analysis/dashboard/app.py"
