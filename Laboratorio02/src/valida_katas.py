"""Valida o catálogo e a coleta dos testes de aceitação das katas."""

from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MANIFESTO = BASE_DIR / "data" / "katas.csv"
CAMPOS = {
    "id",
    "titulo",
    "modulo",
    "funcao",
    "dificuldade_estimada_min",
    "testes_aceitacao",
    "dominio",
    "risco_memorizacao",
}


def carregar_manifesto() -> list[dict[str, str]]:
    with MANIFESTO.open(newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        if set(leitor.fieldnames or ()) != CAMPOS:
            raise ValueError("cabecalho de data/katas.csv nao corresponde ao schema")
        linhas = list(leitor)
    if len(linhas) not in (4, 6):
        raise ValueError("o experimento deve ter exatamente 4 ou 6 katas")
    return linhas


def validar_kata(kata: dict[str, str]) -> None:
    identificador = kata["id"]
    modulo = BASE_DIR / kata["modulo"]
    pasta = modulo.parent
    testes = sorted(pasta.glob("test_*.py"))
    if not modulo.is_file():
        raise ValueError(f"{identificador}: modulo ausente: {kata['modulo']}")
    if not testes:
        raise ValueError(f"{identificador}: nenhum arquivo test_*.py")
    try:
        quantidade = int(kata["testes_aceitacao"])
    except ValueError as erro:
        raise ValueError(f"{identificador}: testes_aceitacao nao e inteiro") from erro
    if quantidade < 6:
        raise ValueError(f"{identificador}: menos de seis testes de aceitacao")

    comando = [sys.executable, "-m", "pytest", "--collect-only", "-q", *map(str, testes)]
    resultado = subprocess.run(comando, cwd=BASE_DIR, capture_output=True, text=True)
    if resultado.returncode != 0:
        detalhes = (resultado.stdout + resultado.stderr).strip()
        raise ValueError(f"{identificador}: pytest nao coletou os testes: {detalhes}")
    coletados = [linha for linha in resultado.stdout.splitlines() if "::" in linha]
    if len(coletados) < quantidade:
        raise ValueError(
            f"{identificador}: esperado pelo menos {quantidade} testes, "
            f"mas pytest coletou {len(coletados)}"
        )


def main() -> int:
    try:
        katas = carregar_manifesto()
        identificadores = [kata["id"] for kata in katas]
        if len(set(identificadores)) != len(identificadores):
            raise ValueError("ids de katas duplicados")
        for kata in katas:
            validar_kata(kata)
    except (OSError, ValueError) as erro:
        print(f"ERRO: {erro}")
        return 1
    print(f"{len(katas)} kata(s) validada(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())