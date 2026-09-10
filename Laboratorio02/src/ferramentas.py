"""
Lab02 - base comum de invocacao das ferramentas externas.

Concentra a chamada das ferramentas de linha de comando usadas na preparacao do
ambiente (src/verifica_ambiente.py) e na coleta das metricas estaticas
(src/metricas_estaticas.py), para que as duas resolvam e executem os mesmos
binarios do mesmo jeito.

O ponto delicado e o Windows, ambiente usado na entrega: npm instala o jscpd e o
VS Code instala a CLI 'code' como shims .CMD, e o CreateProcess do Windows nao
executa .CMD/.BAT diretamente - subprocess.run(["jscpd", ...]) falha com OSError
mesmo com a ferramenta instalada e no PATH. Por isso todo comando passa por
resolve_comando(), que localiza o executavel real e, quando ele e um shim,
prefixa 'cmd /c'. Sem isso, o jscpd seria classificado como ausente e a
duplicacao da RQ03 ficaria sem coleta no Windows.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess

# Extensoes que o Windows so executa por meio do interpretador de comandos.
SHIMS_WINDOWS = (".cmd", ".bat")


def resolve_comando(nome: str) -> list[str] | None:
    """Localiza a ferramenta no PATH e devolve o comando pronto para subprocess.

    Retorna None se ela nao estiver instalada.
    """
    caminho = shutil.which(nome)
    if caminho is None:
        return None
    if os.name == "nt" and caminho.lower().endswith(SHIMS_WINDOWS):
        return ["cmd", "/c", caminho]
    return [caminho]


def executa(nome: str, *argumentos: str, timeout: int = 300) -> tuple[int, str] | None:
    """Roda uma ferramenta externa e devolve (exit_code, saida).

    Retorna None quando a ferramenta nao esta instalada ou nao pode ser
    executada - caso tratado pelos chamadores como "metrica nao coletada", nunca
    como valor zero, para nao contaminar a comparacao entre os tratamentos.
    """
    comando = resolve_comando(nome)
    if comando is None:
        return None
    try:
        proc = subprocess.run(
            comando + list(argumentos),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def saida_ok(resultado: tuple[int, str] | None) -> str | None:
    """Devolve a saida de executa() apenas se o comando terminou com sucesso."""
    if resultado is None:
        return None
    exit_code, saida = resultado
    if exit_code != 0:
        return None
    return saida.strip() or None


def primeira_versao(texto: str | None) -> str:
    """Extrai o primeiro numero de versao (ex.: '1.2.3') de uma saida de --version."""
    if not texto:
        return ""
    m = re.search(r"\d+\.\d+(?:\.\d+)?", texto)
    if m:
        return m.group(0)
    return texto.splitlines()[0].strip()
