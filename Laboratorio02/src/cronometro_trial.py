"""
Cronometragem e coleta de tempo dos trials

Cronometra um trial (kata x tratamento x integrante), aplicando o time-box de
35 min (corte automatico = trial censurado, nunca descartado).
Ao final (parada manual ou censura), executa o comando de teste
do kata e registra o resultado (status final, testes passando/total) junto
com o tempo, exportando os dados brutos para data/trials.csv e data/trials.json.

Uso:
    python src/cronometro_trial.py \
        --integrante "Fulano" \
        --kata "string-calculator" \
        --tratamento com_ia \
        --test-cmd "pytest -q"

    python src/cronometro_trial.py --integrante "Fulano" --kata "fizzbuzz" \
        --tratamento sem_ia --test-cmd "pytest -q" --timebox 20

    # preserva o codigo final em trials/<trial_id>/ automaticamente (passo 5
    # do protocolo em docs/desenho_experimento.md)
    python src/cronometro_trial.py --integrante "Fulano" --kata "fizzbuzz" \
        --tratamento com_ia --test-cmd "pytest trials/_work/fizzbuzz_com_ia" \
        --codigo-dir trials/_work/fizzbuzz_com_ia

Controles durante o trial:
    - pressione ENTER a qualquer momento para encerrar o trial manualmente
      (o script então roda os testes e classifica o resultado).
    - se ninguem pressionar ENTER até o time-box, o trial é encerrado
      automaticamente e marcado como censurado em <timebox> min.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import subprocess
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = DATA_DIR / "logs"
TRIALS_DIR = BASE_DIR / "trials"
CSV_PATH = DATA_DIR / "trials.csv"
JSON_PATH = DATA_DIR / "trials.json"

CSV_COLUMNS = [
    "trial_id",
    "integrante",
    "kata",
    "tratamento",
    "timestamp_inicio",
    "timestamp_fim",
    "tempo_segundos",
    "tempo_minutos",
    "timebox_minutos",
    "status",
    "testes_passando",
    "testes_total",
    "exit_code",
    "test_cmd",
    "log_path",
    "observacoes",
]

TRATAMENTOS_VALIDOS = {"com_ia", "sem_ia"}


@dataclass
class ResultadoTrial:
    trial_id: str
    integrante: str
    kata: str
    tratamento: str
    timestamp_inicio: str
    timestamp_fim: str
    tempo_segundos: float
    tempo_minutos: float
    timebox_minutos: float
    status: str
    testes_passando: int | None
    testes_total: int | None
    exit_code: int
    test_cmd: str
    log_path: str
    observacoes: str = ""


def sanitize(texto: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "-", texto.strip()).strip("-")


def cronometrar(timebox_min: float) -> tuple[float, bool]:
    """Aguarda ENTER (parada manual) ou o time-box (censura). Retorna (segundos, censurado)."""
    stop_event = threading.Event()

    def aguarda_enter():
        try:
            input()
        except EOFError:
            pass
        stop_event.set()

    thread = threading.Thread(target=aguarda_enter, daemon=True)
    thread.start()

    timebox_seg = timebox_min * 60
    inicio = time.monotonic()
    print(
        f"Cronometro iniciado. Pressione ENTER para encerrar o trial, "
        f"ou aguarde o time-box de {timebox_min:.0f} min para censura automatica."
    )
    while not stop_event.is_set():
        decorrido = time.monotonic() - inicio
        if decorrido >= timebox_seg:
            break
        time.sleep(0.2)

    decorrido = time.monotonic() - inicio
    censurado = decorrido >= timebox_seg
    tempo_final = timebox_seg if censurado else decorrido
    return tempo_final, censurado


def parse_resultado_testes(saida: str) -> tuple[int | None, int | None]:
    """Extrai (passando, total) de saidas comuns de test runner (pytest, jest, JUnit/maven, unittest)."""
    m = re.search(r"(\d+)\s+passed", saida)
    if m:
        passando = int(m.group(1))
        mf = re.search(r"(\d+)\s+failed", saida)
        me = re.search(r"(\d+)\s+error", saida)
        falhando = int(mf.group(1)) if mf else 0
        erros = int(me.group(1)) if me else 0
        return passando, passando + falhando + erros

    m = re.search(r"Tests:\s*(?:(\d+)\s+failed,\s*)?(\d+)\s+passed,\s*(\d+)\s+total", saida)
    if m:
        return int(m.group(2)), int(m.group(3))

    m = re.search(
        r"Tests run:\s*(\d+),\s*Failures:\s*(\d+),\s*Errors:\s*(\d+)", saida
    )
    if m:
        total = int(m.group(1))
        falhas = int(m.group(2)) + int(m.group(3))
        return total - falhas, total

    m_ran = re.search(r"Ran\s+(\d+)\s+tests?", saida)
    if m_ran:
        total = int(m_ran.group(1))
        if re.search(r"^OK\b", saida, re.MULTILINE):
            return total, total
        mf = re.search(r"failures=(\d+)", saida)
        me = re.search(r"errors=(\d+)", saida)
        falhas = (int(mf.group(1)) if mf else 0) + (int(me.group(1)) if me else 0)
        return total - falhas, total

    return None, None


def rodar_testes(test_cmd: str, trial_id: str) -> tuple[int, int | None, int | None, str]:
    print(f"Rodando comando de teste: {test_cmd}")
    proc = subprocess.run(test_cmd, shell=True, capture_output=True, text=True)
    saida = (proc.stdout or "") + "\n" + (proc.stderr or "")

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOGS_DIR / f"{trial_id}.log"
    log_path.write_text(saida, encoding="utf-8")

    passando, total = parse_resultado_testes(saida)
    return proc.returncode, passando, total, log_path.relative_to(BASE_DIR).as_posix()


def classificar_status(censurado: bool, exit_code: int) -> str:
    if censurado:
        return "censurado"
    return "passou" if exit_code == 0 else "falhou"


def preservar_codigo(codigo_dir: Path, trial_id: str) -> str:
    """Copia o codigo final do trial para trials/<trial_id>/.

    E la que src/metricas_estaticas.py procura o codigo por convencao (--todos
    ou --trial-id sem --codigo-dir), entao preservar no lugar certo aqui evita
    ter que apontar o caminho manualmente na S03.
    """
    destino = TRIALS_DIR / trial_id
    if destino.exists():
        raise SystemExit(f"{destino} ja existe - nao sobrescrevo o codigo de um trial ja preservado")
    shutil.copytree(
        codigo_dir,
        destino,
        ignore=shutil.ignore_patterns(".venv", "venv", "__pycache__", ".pytest_cache", ".git"),
    )
    return destino.relative_to(BASE_DIR).as_posix()


def salvar_resultado(resultado: ResultadoTrial) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    linhas = []
    if CSV_PATH.exists():
        with CSV_PATH.open("r", newline="", encoding="utf-8") as f:
            linhas = list(csv.DictReader(f))
    linhas.append(asdict(resultado))

    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(linhas)

    with JSON_PATH.open("w", encoding="utf-8") as f:
        json.dump(linhas, f, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--integrante", required=True, help="Nome do integrante que executa o trial")
    parser.add_argument("--kata", required=True, help="Identificador/nome do kata")
    parser.add_argument("--tratamento", required=True, choices=sorted(TRATAMENTOS_VALIDOS), help="com_ia ou sem_ia")
    parser.add_argument("--test-cmd", required=True, help="Comando de shell que roda os testes de aceitacao do kata")
    parser.add_argument("--timebox", type=float, default=35.0, help="Time-box em minutos (default 35; so pode ser reduzido)")
    parser.add_argument("--trial-id", default=None, help="Identificador do trial (default: gerado automaticamente)")
    parser.add_argument("--observacoes", default="", help="Observacoes livres sobre o trial")
    parser.add_argument("--passed", type=int, default=None, help="Override manual de testes passando (fallback se o parser automatico falhar)")
    parser.add_argument("--total", type=int, default=None, help="Override manual do total de testes (fallback se o parser automatico falhar)")
    parser.add_argument("--codigo-dir", default=None, help="Diretorio com o codigo final do trial; se informado, e copiado para trials/<trial_id>/ ao final")
    args = parser.parse_args()

    if args.timebox > 35.0:
        parser.error("--timebox nao pode ser maior que 35 min (enunciado: so pode ser reduzido, nunca aumentado)")

    timestamp_inicio = datetime.now(timezone.utc).isoformat()
    trial_id = args.trial_id or (
        f"{sanitize(args.integrante)}_{sanitize(args.kata)}_{args.tratamento}_"
        f"{datetime.now():%Y%m%dT%H%M%S}"
    )

    tempo_segundos, censurado = cronometrar(args.timebox)
    exit_code, passando, total, log_path = rodar_testes(args.test_cmd, trial_id)

    if passando is None and args.passed is not None:
        passando = args.passed
    if total is None and args.total is not None:
        total = args.total

    status = classificar_status(censurado, exit_code)
    timestamp_fim = datetime.now(timezone.utc).isoformat()

    resultado = ResultadoTrial(
        trial_id=trial_id,
        integrante=args.integrante,
        kata=args.kata,
        tratamento=args.tratamento,
        timestamp_inicio=timestamp_inicio,
        timestamp_fim=timestamp_fim,
        tempo_segundos=round(tempo_segundos, 2),
        tempo_minutos=round(tempo_segundos / 60, 2),
        timebox_minutos=args.timebox,
        status=status,
        testes_passando=passando,
        testes_total=total,
        exit_code=exit_code,
        test_cmd=args.test_cmd,
        log_path=log_path,
        observacoes=args.observacoes,
    )
    salvar_resultado(resultado)

    codigo_preservado = None
    if args.codigo_dir:
        codigo_preservado = preservar_codigo(Path(args.codigo_dir).resolve(), trial_id)

    print("\n--- Trial registrado ---")
    print(f"trial_id:  {resultado.trial_id}")
    print(f"status:    {resultado.status}")
    print(f"tempo:     {resultado.tempo_minutos} min")
    print(f"testes:    {resultado.testes_passando}/{resultado.testes_total}")
    print(f"salvo em:  {CSV_PATH.relative_to(BASE_DIR)} e {JSON_PATH.relative_to(BASE_DIR)}")
    if codigo_preservado:
        print(f"codigo:    {codigo_preservado}")
    else:
        print("codigo:    nao preservado (use --codigo-dir na proxima vez, ou copie manualmente para trials/<trial_id>/)")


if __name__ == "__main__":
    main()
