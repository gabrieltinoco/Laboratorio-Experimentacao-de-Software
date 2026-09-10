"""
Verificacao e registro do ambiente do experimento

Confere se a maquina do integrante esta com o ambiente exigido pelo desenho do
experimento (linguagem, IDE, assistente de IA e ferramentas de metrica estatica)
e registra as versoes encontradas em data/ambiente.csv e data/ambiente.json.

Cada integrante roda este script uma vez antes de comecar os trials da S02. O
snapshot commitado e a evidencia de que os tres executaram o experimento no
mesmo ambiente - condicao para o tratamento (com_ia x sem_ia) ser a unica
diferenca entre os trials, e nao a ferramenta ou a versao da linguagem.

Uso:
    python src/verifica_ambiente.py --integrante "Fulano"

    python src/verifica_ambiente.py --integrante "Fulano" --nao-registrar

Codigo de saida:
    0 - todos os itens obrigatorios presentes (o ambiente esta pronto)
    1 - falta algum item obrigatorio (o proprio relatorio indica qual)
"""

from __future__ import annotations

import argparse
import csv
import json
import platform
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from ferramentas import executa, primeira_versao, saida_ok

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CSV_PATH = DATA_DIR / "ambiente.csv"
JSON_PATH = DATA_DIR / "ambiente.json"

CSV_COLUMNS = [
    "integrante",
    "timestamp_verificacao",
    "sistema_operacional",
    "python_versao",
    "pytest_versao",
    "radon_versao",
    "node_versao",
    "jscpd_versao",
    "ide_versao",
    "assistente_ia",
    "assistente_ia_versao",
    "git_versao",
    "itens_faltando",
    "pronto",
]

# Versao minima da linguagem fixada para as katas. O mesmo piso usado no Lab01.
PYTHON_MINIMO = (3, 10)

# Assistente de IA fixado para todos os trials do grupo (ver docs/ambiente.md).
# So estas extensoes sao inspecionadas - o script nao lista as demais extensoes
# instaladas, que nao fazem parte do desenho do experimento.
ASSISTENTE_IA = "GitHub Copilot"
ASSISTENTE_EXTENSOES = ("github.copilot", "github.copilot-chat")


@dataclass
class Ambiente:
    integrante: str
    timestamp_verificacao: str
    sistema_operacional: str
    python_versao: str
    pytest_versao: str
    radon_versao: str
    node_versao: str
    jscpd_versao: str
    ide_versao: str
    assistente_ia: str
    assistente_ia_versao: str
    git_versao: str
    itens_faltando: str
    pronto: bool


def versao_python() -> str:
    return platform.python_version()


def versao_modulo(modulo: str) -> str:
    """Versao de um modulo Python instalado no interpretador atual (pytest, radon)."""
    return primeira_versao(saida_ok(executa(sys.executable, "-m", modulo, "--version")))


def versao_node() -> str:
    return primeira_versao(saida_ok(executa("node", "--version")))


def versao_jscpd() -> str:
    """Versao do jscpd instalado globalmente pelo npm (nao usa npx, que baixaria on-demand)."""
    return primeira_versao(saida_ok(executa("jscpd", "--version")))


def versao_ide() -> str:
    """Versao do VS Code pela CLI 'code' (primeira linha da saida de --version)."""
    return primeira_versao(saida_ok(executa("code", "--version")))


def versao_assistente() -> str:
    """Versao da extensao do assistente de IA fixado, lida da lista de extensoes do VS Code."""
    saida = saida_ok(executa("code", "--list-extensions", "--show-versions"))
    if not saida:
        return ""
    for linha in saida.splitlines():
        nome, _, versao = linha.strip().partition("@")
        if nome.strip().lower() in ASSISTENTE_EXTENSOES:
            return versao.strip()
    return ""


def versao_git() -> str:
    return primeira_versao(saida_ok(executa("git", "--version")))


def coleta_ambiente(integrante: str) -> Ambiente:
    python = versao_python()
    pytest_v = versao_modulo("pytest")
    radon_v = versao_modulo("radon")
    node_v = versao_node()
    jscpd_v = versao_jscpd()
    ide_v = versao_ide()
    assistente_v = versao_assistente()
    git_v = versao_git()

    # Itens obrigatorios: sem qualquer um deles um trial da S02 nao pode ser
    # executado ou nao pode ser medido, o que inviabilizaria a comparacao.
    faltando: list[str] = []
    if tuple(int(p) for p in python.split(".")[:2]) < PYTHON_MINIMO:
        faltando.append(
            f"python >= {PYTHON_MINIMO[0]}.{PYTHON_MINIMO[1]} (encontrado {python})"
        )
    if not pytest_v:
        faltando.append("pytest (pip install -r src/requirements.txt)")
    if not radon_v:
        faltando.append("radon (pip install -r src/requirements.txt)")
    if not node_v:
        faltando.append("node (necessario para o jscpd)")
    if not jscpd_v:
        faltando.append("jscpd (npm install -g jscpd)")
    if not ide_v:
        faltando.append("VS Code com a CLI 'code' no PATH")
    if not assistente_v:
        faltando.append(f"{ASSISTENTE_IA} ({'/'.join(ASSISTENTE_EXTENSOES)})")
    if not git_v:
        faltando.append("git")

    return Ambiente(
        integrante=integrante,
        timestamp_verificacao=datetime.now(timezone.utc).isoformat(),
        sistema_operacional=f"{platform.system()} {platform.release()}",
        python_versao=python,
        pytest_versao=pytest_v,
        radon_versao=radon_v,
        node_versao=node_v,
        jscpd_versao=jscpd_v,
        ide_versao=ide_v,
        assistente_ia=ASSISTENTE_IA,
        assistente_ia_versao=assistente_v,
        git_versao=git_v,
        itens_faltando="; ".join(faltando),
        pronto=not faltando,
    )


def salvar_ambiente(ambiente: Ambiente) -> None:
    """Grava o snapshot, substituindo a linha anterior do mesmo integrante."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    linhas = []
    if CSV_PATH.exists():
        with CSV_PATH.open("r", newline="", encoding="utf-8") as f:
            linhas = [
                linha
                for linha in csv.DictReader(f)
                if linha.get("integrante") != ambiente.integrante
            ]
    linhas.append({k: str(v) for k, v in asdict(ambiente).items()})

    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(linhas)

    with JSON_PATH.open("w", encoding="utf-8") as f:
        json.dump(linhas, f, ensure_ascii=False, indent=2)


def imprime_relatorio(ambiente: Ambiente) -> None:
    itens = [
        ("Sistema operacional", ambiente.sistema_operacional, True),
        ("Python (linguagem das katas)", ambiente.python_versao, True),
        ("pytest (testes de aceitacao)", ambiente.pytest_versao, bool(ambiente.pytest_versao)),
        ("radon (complexidade/LOC/MI)", ambiente.radon_versao, bool(ambiente.radon_versao)),
        ("node (runtime do jscpd)", ambiente.node_versao, bool(ambiente.node_versao)),
        ("jscpd (duplicacao)", ambiente.jscpd_versao, bool(ambiente.jscpd_versao)),
        ("VS Code (IDE)", ambiente.ide_versao, bool(ambiente.ide_versao)),
        (f"{ambiente.assistente_ia} (tratamento com_ia)", ambiente.assistente_ia_versao, bool(ambiente.assistente_ia_versao)),
        ("git", ambiente.git_versao, bool(ambiente.git_versao)),
    ]

    print(f"--- Ambiente de {ambiente.integrante} ---")
    for nome, valor, ok in itens:
        marca = "OK  " if ok else "FALTA"
        print(f"  [{marca}] {nome}: {valor or '(nao encontrado)'}")

    if ambiente.pronto:
        print("\nAmbiente pronto para os trials da S02.")
    else:
        print("\nPendencias antes de rodar qualquer trial:")
        for item in ambiente.itens_faltando.split("; "):
            print(f"  - {item}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--integrante", required=True, help="Nome do integrante cuja maquina esta sendo verificada")
    parser.add_argument("--nao-registrar", action="store_true", help="Apenas imprime o relatorio, sem gravar em data/ambiente.csv")
    args = parser.parse_args()

    ambiente = coleta_ambiente(args.integrante)
    imprime_relatorio(ambiente)

    if not args.nao_registrar:
        salvar_ambiente(ambiente)
        print(f"\nSnapshot salvo em {CSV_PATH.relative_to(BASE_DIR)} e {JSON_PATH.relative_to(BASE_DIR)}")

    raise SystemExit(0 if ambiente.pronto else 1)


if __name__ == "__main__":
    main()
