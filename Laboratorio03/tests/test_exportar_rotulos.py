"""Testes de exportação da planilha de rótulos independente."""

from __future__ import annotations

import pandas as pd
import pytest

from validacao.exportar_rotulos import exportar


def criar_planilha(caminho, *, corretiva="sim"):
    repositorios = pd.DataFrame(
        [{
            "repositorio": "o/r",
            "link": "https://github.com/o/r",
            "tipo_projeto": "biblioteca/framework",
            "entregas_reais": "sim",
            "observacoes": "pacote publicado",
        }]
    )
    releases = pd.DataFrame(
        [{
            "repositorio": "o/r",
            "tag_name": "v1.0.1",
            "publicada_em": "2026-01-02",
            "link_release": "https://github.com/o/r/releases/tag/v1.0.1",
            "link_commits": "https://github.com/o/r/compare/v1.0.0...v1.0.1",
            "corretiva": corretiva,
            "observacoes": "corrige regressão",
        }]
    )
    with pd.ExcelWriter(caminho) as writer:
        repositorios.to_excel(writer, sheet_name="repositorios", index=False)
        releases.to_excel(writer, sheet_name="releases", index=False)


def test_exporta_rotulos_em_uma_linha_por_release(tmp_path):
    planilha = tmp_path / "rotulos.xlsx"
    destino = tmp_path / "rotulos_B.csv"
    criar_planilha(planilha)

    resultado = exportar(planilha, destino)

    assert len(resultado) == 1
    assert resultado.loc[0, "tipo_projeto"] == "biblioteca/framework"
    assert resultado.loc[0, "corretiva"] == "sim"
    assert resultado.loc[0, "observacoes_repositorio"] == "pacote publicado"
    assert resultado.loc[0, "observacoes_release"] == "corrige regressão"
    assert pd.read_csv(destino).equals(resultado)


def test_nao_exporta_planilha_com_rotulo_invalido(tmp_path):
    planilha = tmp_path / "rotulos.xlsx"
    criar_planilha(planilha, corretiva="")

    with pytest.raises(ValueError, match="rótulos vazios ou inválidos"):
        exportar(planilha, tmp_path / "rotulos_B.csv")
