from collections import Counter
from typing import Mapping
import pandas as pd


def run_is_valid(row: Mapping) -> bool:
    error = str(row.get("error", "") or "").strip()
    timeout = bool(row.get("timeout", False))
    if error:
        return False
    return bool(timeout or row.get("valid", True))


def validate(df: pd.DataFrame, cfg: dict, phase: str) -> list[str]:
    problems = []
    if df is None or df.empty:
        return ["PROBLEMA: resultados vazios"]
    if "run_id" in df.columns:
        duplicate_ids = df[df.duplicated("run_id", keep=False)]
        if not duplicate_ids.empty:
            problems.append("PROBLEMA: run_id duplicado")
    if "error" in df.columns:
        errors = df[df["error"].fillna("").astype(str).str.strip() != ""]
        if not errors.empty:
            problems.append("PROBLEMA: resultado com erro")
    if "timeout" in df.columns:
        timeouts = df[df["timeout"] == True]
        if not timeouts.empty:
            problems.append("INFO timeouts: " + str(len(timeouts)) + " item(s) marcados")
    if "valid" in df.columns:
        invalid = df[df["valid"] == False]
        if not invalid.empty:
            problems.append(f"PROBLEMA: {len(invalid)} resultado(s) inválido(s)")
    if "run_id" in df.columns:
        expected = len(df["run_id"].drop_duplicates())
        if df.shape[0] != expected:
            problems.append("PROBLEMA: número de repetições inconsistente")
    return problems
