"""
Runner unico por trial da S02

Encapsula os passos manuais do roteiro em docs/execucao_integrante_a.md em um
unico comando por trial, para reduzir erro de protocolo sob pressao de tempo:

    1. copia o esqueleto da kata da sequencia atribuida para uma pasta de
       trabalho em trials/_work/<kata>_<tratamento>/ (pula se ja existir);
    2. abre essa pasta no VS Code, ja com o Copilot ligado ou desligado
       conforme o tratamento do trial;
    3. so inicia o cronometro depois que voce confirmar (ENTER) que esta
       pronto para comecar a resolver - o tempo de abrir o editor nao conta;
    4. chama src/cronometro_trial.py com --kata, --tratamento, --test-cmd e
       --codigo-dir ja preenchidos corretamente, preservando o codigo final em
       trials/<trial_id>/ ao final.

Uso:
    python src/executar_trial.py gabitolage 1
    python src/executar_trial.py art1544 3 --issue 42
    python src/executar_trial.py gabrieltinoco 2 --timebox 20

O primeiro argumento identifica quem esta rodando o trial e ja resolve a
sequencia contrabalanceada dele (ver INTEGRANTES/SEQUENCIAS abaixo) - nao
precisa mais passar --integrante nem soletrar a sequencia na mao.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
KATAS_DIR = BASE_DIR / "katas"
TRIALS_DIR = BASE_DIR / "trials"
WORK_DIR = TRIALS_DIR / "_work"
CRONOMETRO = Path(__file__).resolve().parent / "cronometro_trial.py"

# Sequencias do desenho experimental (docs/desenho_experimento.md): kata x
# tratamento por indice 1-based.
SEQUENCIAS = {
    "A": [
        ("fila-prioridade", "com_ia"),
        ("janela-cobranca", "sem_ia"),
        ("agenda-recorrente", "com_ia"),
        ("roteador-notificacoes", "sem_ia"),
    ],
    "B": [
        ("fila-prioridade", "sem_ia"),
        ("janela-cobranca", "com_ia"),
        ("agenda-recorrente", "sem_ia"),
        ("roteador-notificacoes", "com_ia"),
    ],
    "C": [
        ("fila-prioridade", "com_ia"),
        ("janela-cobranca", "com_ia"),
        ("agenda-recorrente", "sem_ia"),
        ("roteador-notificacoes", "sem_ia"),
    ],
}

# Usuario do GitHub -> nome gravado em data/trials.csv e sequencia atribuida.
# Distribuicao default (A, B, C): ajuste aqui se o trio ja tiver combinado
# outra atribuicao entre os tres antes de comecar os trials.
INTEGRANTES = {
    "gabitolage": {"nome": "gabitolage", "sequencia": "A"},
    "art1544": {"nome": "Arthur Miranda Pacher", "sequencia": "B"},
    "gabrieltinoco": {"nome": "Gabriel L. Tinoco", "sequencia": "C"},
}

IGNORAR_AO_COPIAR = shutil.ignore_patterns(".venv", "venv", "__pycache__", ".pytest_cache", ".git")


def preparar_pasta_trabalho(kata: str, tratamento: str, recriar: bool) -> Path:
    kata_src = KATAS_DIR / kata
    if not kata_src.is_dir():
        raise SystemExit(f"kata '{kata}' nao encontrada em {kata_src}")

    destino = WORK_DIR / f"{kata}_{tratamento}"
    if destino.exists():
        if not recriar:
            print(f"Pasta de trabalho ja existe, reaproveitando: {destino.relative_to(BASE_DIR)}")
            return destino
        shutil.rmtree(destino)

    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(kata_src, destino, ignore=IGNORAR_AO_COPIAR)
    print(f"Esqueleto copiado para {destino.relative_to(BASE_DIR)}")
    return destino


def abrir_editor(pasta: Path, tratamento: str) -> None:
    if tratamento == "com_ia":
        cmd = ["code", str(pasta)]
    else:
        cmd = ["code", "--disable-extension", "github.copilot", str(pasta)]

    print("Comando para abrir o editor:", " ".join(cmd))
    try:
        subprocess.Popen(cmd, shell=(os.name == "nt"))
    except OSError:
        print("Nao encontrei o comando 'code' no PATH - abra a pasta acima manualmente no VS Code.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("integrante", choices=sorted(INTEGRANTES), help="Usuario do GitHub de quem esta executando o trial (define a sequencia automaticamente)")
    parser.add_argument("indice", type=int, help="Numero do trial na sequencia (1 a 4)")
    parser.add_argument("--issue", type=int, default=None, help="Numero da Issue do GitHub Projects para este trial")
    parser.add_argument("--timebox", type=float, default=35.0, help="Time-box em minutos (default 35; so pode ser reduzido)")
    parser.add_argument("--recriar", action="store_true", help="Apaga e recopia a pasta de trabalho, mesmo se ja existir")
    args = parser.parse_args()

    info = INTEGRANTES[args.integrante]
    sequencia = SEQUENCIAS[info["sequencia"]]

    if not (1 <= args.indice <= len(sequencia)):
        parser.error(f"indice deve estar entre 1 e {len(sequencia)}")

    kata, tratamento = sequencia[args.indice - 1]

    print(f"--- {info['nome']} | sequencia {info['sequencia']} | trial {args.indice}/{len(sequencia)}: {kata} ({tratamento}) ---")
    pasta = preparar_pasta_trabalho(kata, tratamento, args.recriar)
    abrir_editor(pasta, tratamento)

    input(
        "\nPressione ENTER quando o editor estiver aberto (Copilot conferido) e "
        "voce estiver pronto para comecar a resolver - o cronometro so inicia agora.\n"
    )

    pasta_relativa = pasta.relative_to(BASE_DIR).as_posix()
    cmd = [
        sys.executable,
        str(CRONOMETRO),
        "--integrante", info["nome"],
        "--kata", kata,
        "--tratamento", tratamento,
        "--test-cmd", f"pytest {pasta_relativa}",
        "--codigo-dir", pasta_relativa,
        "--timebox", str(args.timebox),
    ]
    if args.issue is not None:
        cmd += ["--observacoes", f"issue #{args.issue}"]

    resultado = subprocess.run(cmd, cwd=BASE_DIR)
    raise SystemExit(resultado.returncode)


if __name__ == "__main__":
    main()
