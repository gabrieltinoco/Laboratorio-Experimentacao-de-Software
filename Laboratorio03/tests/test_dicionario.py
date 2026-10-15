"""Toda coluna dos CSVs finais precisa estar documentada em dados/DICIONARIO.md."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import pytest

import pipeline.__main__ as principal
from tests.test_pipeline import ClienteFalso, config

DICIONARIO = Path(__file__).resolve().parents[1] / "dados" / "DICIONARIO.md"


def documentadas() -> set[str]:
    return set(re.findall(r"`([a-z0-9_]+)`", DICIONARIO.read_text(encoding="utf-8")))


@pytest.mark.parametrize("arquivo", ["repositorios.csv", "metadados.csv", "funil.csv", "descartes.csv"])
def test_colunas_dos_csvs_estao_no_dicionario(tmp_path, arquivo):
    principal.executar(config(tmp_path), ClienteFalso())
    colunas = pd.read_csv(tmp_path / "dados" / arquivo).columns

    assert set(colunas) - documentadas() == set()
