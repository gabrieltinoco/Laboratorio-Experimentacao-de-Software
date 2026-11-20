from pathlib import Path
from typing import Literal


def load_query(engine_kind: Literal["duckdb", "sqlite"], qid: str) -> str:
    if engine_kind not in {"duckdb", "sqlite"}:
        raise ValueError(f"unsupported engine kind: {engine_kind}")
    if not qid.startswith("q") or not qid[1:].isdigit():
        raise ValueError(f"invalid query id: {qid}")
    path = Path(__file__).resolve().parent / "queries" / engine_kind / f"{qid}.sql"
    if not path.exists():
        raise FileNotFoundError(path)
    return "\n".join(
        line for line in path.read_text(encoding="utf-8").splitlines()
        if not line.startswith("--")
    ).strip()