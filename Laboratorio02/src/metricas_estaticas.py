"""
Coleta das metricas estaticas dos trials (RQ03)

Roda as ferramentas de metrica estatica sobre o codigo final de um trial e
consolida o resultado em data/metricas.csv e data/metricas.json, uma linha por
trial, com o mesmo trial_id usado pelo cronometro - o que permite juntar as duas
tabelas na analise da S03.

Metricas coletadas (ver docs/metricas_estaticas.md):
    - complexidade ciclomatica por funcao/metodo (radon cc): media, mediana, max
      e total;
    - LOC e SLOC (radon raw), metrica de controle obrigatoria sempre que se
      reporta complexidade ou duplicacao;
    - Indice de Manutenibilidade (radon mi), metrica opcional de aprofundamento;
    - percentual de linhas duplicadas (jscpd), equivalente ao PMD CPD fora do
      Java.

Uso:
    python src/metricas_estaticas.py --trial-id Fulano_fizzbuzz_com_ia_20260910T143201

    python src/metricas_estaticas.py --trial-id <id> --codigo-dir caminho/para/o/codigo

    python src/metricas_estaticas.py --todos

Por convencao, o codigo final de cada trial fica em trials/<trial_id>/ e e
localizado automaticamente; --codigo-dir serve para os casos em que o codigo
esteja em outro lugar.

Os testes de aceitacao da kata sao excluidos da medicao: eles vem prontos com a
kata, sao identicos nos dois tratamentos e diluiriam as metricas do codigo que o
integrante realmente escreveu.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from ferramentas import executa, primeira_versao, saida_ok

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
TRIALS_DIR = BASE_DIR / "trials"
CSV_PATH = DATA_DIR / "metricas.csv"
JSON_PATH = DATA_DIR / "metricas.json"

# Tabela de tempo/testes produzida por src/cronometro_trial.py. E a fonte de
# integrante, kata e tratamento: esses campos nunca sao redigitados aqui, para
# que as duas tabelas nao divirjam.
TRIALS_CSV = DATA_DIR / "trials.csv"

CSV_COLUMNS = [
    "trial_id",
    "integrante",
    "kata",
    "tratamento",
    "codigo_dir",
    "arquivos_analisados",
    "arquivos",
    "loc",
    "sloc",
    "linhas_comentario",
    "linhas_branco",
    "funcoes",
    "cc_media",
    "cc_mediana",
    "cc_max",
    "cc_total",
    "cc_total_por_kloc",
    "mi_medio",
    "dup_percentual",
    "dup_linhas",
    "dup_clones",
    "radon_versao",
    "jscpd_versao",
    "jscpd_min_lines",
    "jscpd_min_tokens",
    "timestamp_coleta",
    "observacoes",
]

# Arquivos de teste da kata: excluidos da medicao (ver docstring).
EXCLUIR_PADRAO = ("test_*.py", "*_test.py", "conftest.py")

# Diretorios que nunca contem codigo escrito pelo integrante no trial.
IGNORAR_DIRS = (".venv", "venv", "__pycache__", ".pytest_cache", ".git", "node_modules", "tests")

# Parametros de deteccao do jscpd. Sao os defaults da ferramenta, fixados aqui e
# registrados no CSV: mudar o minimo de linhas/tokens muda o percentual de
# duplicacao, e a comparacao entre tratamentos so vale com o mesmo parametro.
JSCPD_MIN_LINES = 5
JSCPD_MIN_TOKENS = 50


@dataclass
class MetricasTrial:
    trial_id: str
    integrante: str
    kata: str
    tratamento: str
    codigo_dir: str
    arquivos_analisados: int
    arquivos: str
    loc: int | None
    sloc: int | None
    linhas_comentario: int | None
    linhas_branco: int | None
    funcoes: int | None
    cc_media: float | None
    cc_mediana: float | None
    cc_max: int | None
    cc_total: int | None
    cc_total_por_kloc: float | None
    mi_medio: float | None
    dup_percentual: float | None
    dup_linhas: int | None
    dup_clones: int | None
    radon_versao: str
    jscpd_versao: str
    jscpd_min_lines: int
    jscpd_min_tokens: int
    timestamp_coleta: str
    observacoes: str = ""


def arquivos_do_trial(codigo_dir: Path, excluir: tuple[str, ...]) -> list[Path]:
    """Lista os .py escritos pelo integrante, fora dos diretorios e padroes ignorados.

    A lista e calculada aqui e passada explicitamente as duas ferramentas, em vez
    de deixar cada uma aplicar seus proprios filtros: se o radon e o jscpd
    analisassem conjuntos diferentes de arquivos, o percentual de duplicacao e o
    LOC que o normaliza teriam bases diferentes.
    """
    arquivos = []
    for caminho in sorted(codigo_dir.rglob("*.py")):
        if any(parte in IGNORAR_DIRS for parte in caminho.parts):
            continue
        if any(caminho.match(padrao) for padrao in excluir):
            continue
        arquivos.append(caminho)
    return arquivos


def radon_json(subcomando: str, arquivos: list[Path]) -> dict:
    """Roda 'radon <subcomando> -j' sobre a lista de arquivos e devolve o JSON."""
    saida = saida_ok(
        executa(sys.executable, "-m", "radon", subcomando, "-j", *[str(a) for a in arquivos])
    )
    if not saida:
        return {}
    try:
        return json.loads(saida)
    except json.JSONDecodeError:
        return {}


def blocos_de_complexidade(entradas: list[dict]):
    """Percorre a saida do radon cc rendendo um bloco por funcao/metodo.

    Duas particularidades do formato do radon tratadas aqui:

    1. Entradas de tipo 'class' sao agregados da classe e seus metodos aparecem
       repetidos no nivel de cima da lista - contar a classe geraria contagem
       dupla, por isso ela e ignorada.
    2. Funcoes internas (closures) NAO aparecem no nivel de cima, so aninhadas
       em 'closures' - por isso ha recursao nesse campo.
    """
    for entrada in entradas:
        if entrada.get("type") == "class":
            continue
        yield entrada
        yield from blocos_de_complexidade(entrada.get("closures", []))


def coleta_complexidade(arquivos: list[Path]) -> dict:
    """Complexidade ciclomatica (McCabe) por funcao/metodo, agregada por trial."""
    relatorio = radon_json("cc", arquivos)
    complexidades = [
        bloco["complexity"]
        for entradas in relatorio.values()
        if isinstance(entradas, list)
        for bloco in blocos_de_complexidade(entradas)
        if "complexity" in bloco
    ]
    if not complexidades:
        return {"funcoes": 0, "cc_media": None, "cc_mediana": None, "cc_max": None, "cc_total": None}
    return {
        "funcoes": len(complexidades),
        "cc_media": round(statistics.mean(complexidades), 2),
        "cc_mediana": statistics.median(complexidades),
        "cc_max": max(complexidades),
        "cc_total": sum(complexidades),
    }


def coleta_raw(arquivos: list[Path]) -> dict:
    """LOC, SLOC, comentarios e linhas em branco, somados nos arquivos do trial."""
    relatorio = radon_json("raw", arquivos)
    metricas = [m for m in relatorio.values() if isinstance(m, dict) and "sloc" in m]
    if not metricas:
        return {"loc": None, "sloc": None, "linhas_comentario": None, "linhas_branco": None}
    return {
        "loc": sum(m["loc"] for m in metricas),
        "sloc": sum(m["sloc"] for m in metricas),
        "linhas_comentario": sum(m["single_comments"] + m["multi"] for m in metricas),
        "linhas_branco": sum(m["blank"] for m in metricas),
    }


def coleta_mi(arquivos: list[Path]) -> float | None:
    """Indice de Manutenibilidade medio entre os arquivos do trial."""
    relatorio = radon_json("mi", arquivos)
    valores = [m["mi"] for m in relatorio.values() if isinstance(m, dict) and "mi" in m]
    if not valores:
        return None
    return round(statistics.mean(valores), 2)


def coleta_duplicacao(arquivos: list[Path], min_lines: int, min_tokens: int) -> dict:
    """Percentual de linhas duplicadas, linhas duplicadas e numero de clones (jscpd)."""
    vazio = {"dup_percentual": None, "dup_linhas": None, "dup_clones": None}

    with tempfile.TemporaryDirectory() as tmp:
        resultado = executa(
            "jscpd",
            *[str(a) for a in arquivos],
            "--reporters", "json",
            "--output", tmp,
            "--min-lines", str(min_lines),
            "--min-tokens", str(min_tokens),
            "--silent",
        )
        if resultado is None:
            return vazio

        # O jscpd sai com codigo != 0 quando o percentual passa do --threshold,
        # o que nao e erro de coleta: o relatorio ja esta escrito e e lido de
        # qualquer forma.
        relatorio_path = Path(tmp) / "jscpd-report.json"
        if not relatorio_path.exists():
            return vazio
        try:
            total = json.loads(relatorio_path.read_text(encoding="utf-8"))["statistics"]["total"]
        except (json.JSONDecodeError, KeyError, OSError):
            return vazio

    return {
        "dup_percentual": round(total.get("percentage", 0.0), 2),
        "dup_linhas": total.get("duplicatedLines"),
        "dup_clones": total.get("clones"),
    }


def carrega_trials() -> dict[str, dict]:
    """Indexa data/trials.csv por trial_id (vazio se o cronometro ainda nao rodou)."""
    if not TRIALS_CSV.exists():
        return {}
    with TRIALS_CSV.open("r", newline="", encoding="utf-8") as f:
        return {linha["trial_id"]: linha for linha in csv.DictReader(f)}


def coleta_metricas(
    trial_id: str,
    codigo_dir: Path,
    dados_trial: dict,
    excluir: tuple[str, ...],
    min_lines: int,
    min_tokens: int,
    observacoes: str,
) -> MetricasTrial:
    arquivos = arquivos_do_trial(codigo_dir, excluir)
    nomes = ";".join(a.relative_to(codigo_dir).as_posix() for a in arquivos)

    complexidade = {"funcoes": 0, "cc_media": None, "cc_mediana": None, "cc_max": None, "cc_total": None}
    raw = {"loc": None, "sloc": None, "linhas_comentario": None, "linhas_branco": None}
    mi_medio = None
    duplicacao = {"dup_percentual": None, "dup_linhas": None, "dup_clones": None}
    avisos = [observacoes] if observacoes else []

    if arquivos:
        complexidade = coleta_complexidade(arquivos)
        raw = coleta_raw(arquivos)
        mi_medio = coleta_mi(arquivos)
        duplicacao = coleta_duplicacao(arquivos, min_lines, min_tokens)
        if duplicacao["dup_percentual"] is None:
            avisos.append("duplicacao nao coletada (jscpd indisponivel)")
    else:
        avisos.append("nenhum arquivo .py elegivel no diretorio do trial")

    # Densidade de complexidade: o enunciado exige normalizar por LOC, porque
    # codigo gerado por assistente tende a ser mais verboso e um cc_total maior
    # pode ser so efeito do tamanho.
    cc_total_por_kloc = None
    if complexidade["cc_total"] is not None and raw["sloc"]:
        cc_total_por_kloc = round(complexidade["cc_total"] / (raw["sloc"] / 1000), 2)

    return MetricasTrial(
        trial_id=trial_id,
        integrante=dados_trial.get("integrante", ""),
        kata=dados_trial.get("kata", ""),
        tratamento=dados_trial.get("tratamento", ""),
        codigo_dir=codigo_dir.relative_to(BASE_DIR).as_posix() if codigo_dir.is_relative_to(BASE_DIR) else str(codigo_dir),
        arquivos_analisados=len(arquivos),
        arquivos=nomes,
        loc=raw["loc"],
        sloc=raw["sloc"],
        linhas_comentario=raw["linhas_comentario"],
        linhas_branco=raw["linhas_branco"],
        funcoes=complexidade["funcoes"],
        cc_media=complexidade["cc_media"],
        cc_mediana=complexidade["cc_mediana"],
        cc_max=complexidade["cc_max"],
        cc_total=complexidade["cc_total"],
        cc_total_por_kloc=cc_total_por_kloc,
        mi_medio=mi_medio,
        dup_percentual=duplicacao["dup_percentual"],
        dup_linhas=duplicacao["dup_linhas"],
        dup_clones=duplicacao["dup_clones"],
        radon_versao=primeira_versao(saida_ok(executa(sys.executable, "-m", "radon", "--version"))),
        jscpd_versao=primeira_versao(saida_ok(executa("jscpd", "--version"))),
        jscpd_min_lines=min_lines,
        jscpd_min_tokens=min_tokens,
        timestamp_coleta=datetime.now(timezone.utc).isoformat(),
        observacoes="; ".join(avisos),
    )


def salvar_metricas(metricas: list[MetricasTrial]) -> None:
    """Grava as linhas coletadas, substituindo a linha anterior do mesmo trial_id."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    novos = {m.trial_id for m in metricas}
    linhas = []
    if CSV_PATH.exists():
        with CSV_PATH.open("r", newline="", encoding="utf-8") as f:
            linhas = [linha for linha in csv.DictReader(f) if linha.get("trial_id") not in novos]
    linhas.extend({k: "" if v is None else str(v) for k, v in asdict(m).items()} for m in metricas)

    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(linhas)

    with JSON_PATH.open("w", encoding="utf-8") as f:
        json.dump(linhas, f, ensure_ascii=False, indent=2)


def imprime_metricas(m: MetricasTrial) -> None:
    def v(valor) -> str:
        """Metrica nao coletada aparece como '-', nunca como 0 ou None."""
        return "-" if valor is None else str(valor)

    print(f"\n--- {m.trial_id} ---")
    print(f"  arquivos:     {m.arquivos_analisados} ({m.arquivos or 'nenhum'})")
    print(f"  LOC / SLOC:   {v(m.loc)} / {v(m.sloc)}")
    print(f"  funcoes:      {v(m.funcoes)}")
    print(f"  CC media:     {v(m.cc_media)} (mediana {v(m.cc_mediana)}, max {v(m.cc_max)}, total {v(m.cc_total)})")
    print(f"  CC por KLOC:  {v(m.cc_total_por_kloc)}")
    print(f"  MI medio:     {v(m.mi_medio)}")
    print(f"  duplicacao:   {v(m.dup_percentual)}% ({v(m.dup_linhas)} linhas em {v(m.dup_clones)} clones)")
    if m.observacoes:
        print(f"  observacoes:  {m.observacoes}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--trial-id", help="Identificador do trial, o mesmo usado em data/trials.csv")
    parser.add_argument("--codigo-dir", default=None, help="Diretorio do codigo final (default: trials/<trial_id>)")
    parser.add_argument("--todos", action="store_true", help="Coleta as metricas de todos os trials de data/trials.csv")
    parser.add_argument("--integrante", default=None, help="Sobrescreve o integrante (quando o trial ainda nao esta em trials.csv)")
    parser.add_argument("--kata", default=None, help="Sobrescreve a kata (quando o trial ainda nao esta em trials.csv)")
    parser.add_argument("--tratamento", default=None, help="Sobrescreve o tratamento (quando o trial ainda nao esta em trials.csv)")
    parser.add_argument("--excluir", default=",".join(EXCLUIR_PADRAO), help="Padroes de arquivo excluidos da medicao, separados por virgula")
    parser.add_argument("--min-lines", type=int, default=JSCPD_MIN_LINES, help=f"Minimo de linhas de um clone para o jscpd (default {JSCPD_MIN_LINES})")
    parser.add_argument("--min-tokens", type=int, default=JSCPD_MIN_TOKENS, help=f"Minimo de tokens de um clone para o jscpd (default {JSCPD_MIN_TOKENS})")
    parser.add_argument("--observacoes", default="", help="Observacoes livres sobre a coleta")
    parser.add_argument("--nao-registrar", action="store_true", help="Apenas imprime as metricas, sem gravar em data/metricas.csv")
    args = parser.parse_args()

    if bool(args.trial_id) == bool(args.todos):
        parser.error("informe --trial-id <id> ou --todos (um dos dois)")

    if not saida_ok(executa(sys.executable, "-m", "radon", "--version")):
        parser.error("radon nao encontrado - rode 'python src/verifica_ambiente.py --integrante <nome>' antes")

    excluir = tuple(p.strip() for p in args.excluir.split(",") if p.strip())
    trials = carrega_trials()

    if args.todos:
        alvos = [(tid, TRIALS_DIR / tid) for tid in trials]
        if not alvos:
            parser.error(f"{TRIALS_CSV.relative_to(BASE_DIR)} nao tem trials registrados ainda")
    else:
        codigo_dir = Path(args.codigo_dir).resolve() if args.codigo_dir else TRIALS_DIR / args.trial_id
        alvos = [(args.trial_id, codigo_dir)]

    coletadas: list[MetricasTrial] = []
    ignorados: list[str] = []
    for trial_id, codigo_dir in alvos:
        if not codigo_dir.is_dir():
            ignorados.append(f"{trial_id} (sem codigo em {codigo_dir})")
            continue
        dados_trial = dict(trials.get(trial_id, {}))
        for campo, valor in (("integrante", args.integrante), ("kata", args.kata), ("tratamento", args.tratamento)):
            if valor:
                dados_trial[campo] = valor
        metricas = coleta_metricas(trial_id, codigo_dir, dados_trial, excluir, args.min_lines, args.min_tokens, args.observacoes)
        imprime_metricas(metricas)
        coletadas.append(metricas)

    if ignorados:
        print("\nTrials sem codigo para medir (nada gravado para eles):")
        for item in ignorados:
            print(f"  - {item}")

    if not coletadas:
        raise SystemExit(1)

    if not args.nao_registrar:
        salvar_metricas(coletadas)
        print(f"\n{len(coletadas)} trial(s) gravado(s) em {CSV_PATH.relative_to(BASE_DIR)} e {JSON_PATH.relative_to(BASE_DIR)}")


if __name__ == "__main__":
    main()
