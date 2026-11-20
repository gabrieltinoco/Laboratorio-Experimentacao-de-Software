import argparse
import json
import shutil
import subprocess
from pathlib import Path
import sys

import yaml

from bench.schedule import build_schedule, Block
from bench.runner import run_block


def pending(schedule: list[Block], out_dir: Path) -> list[Block]:
    remaining = []
    for block in schedule:
        path = Path(out_dir) / f"{block.block_id}.json"
        if not path.exists():
            remaining.append(block)
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not data.get("complete"):
                remaining.append(block)
        except (json.JSONDecodeError, OSError):
            remaining.append(block)
    return remaining


def preflight(cfg: dict, cpu_count=None, mem_gb=None, free_disk_gb=None) -> None:
    import psutil
    import shutil

    cpu_count = psutil.cpu_count(logical=True) if cpu_count is None else cpu_count
    mem_gb = psutil.virtual_memory().total / (1024 ** 3) if mem_gb is None else mem_gb
    free_disk_gb = shutil.disk_usage(Path.cwd()).free / (1024 ** 3) if free_disk_gb is None else free_disk_gb
    limits = cfg["limits"]
    if cpu_count < limits["cpus"]:
        raise SystemExit(f"Preflight falhou: CPUs={cpu_count}, necessário >= {limits['cpus']}")
    if mem_gb < limits["mem_gb"] + 2:
        raise SystemExit(f"Preflight falhou: RAM={mem_gb:.1f} GB, necessário >= {limits['mem_gb'] + 2} GB")
    if free_disk_gb < 10:
        raise SystemExit(f"Preflight falhou: disco livre={free_disk_gb:.1f} GB, necessário >= 10 GB")


def execute_block(block: Block, cfg: dict, out_dir: Path) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{block.block_id}.json"
    if block.workload == "oltp":
        engine_kind = cfg["engines"][block.engine]["kind"]
        source = Path("data/db") / f"tpch_sf{block.sf}.{ 'duckdb' if engine_kind == 'duckdb' else 'sqlite' }"
        copy = Path("data/db") / f"{block.block_id}.{source.suffix.lstrip('.')}"
        shutil.copy2(source, copy)
    result = run_block(block, cfg)
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return path


def append_results(raw_json: Path, csv_path: Path, reference_hashes: dict) -> None:
    import pandas as pd

    raw = json.loads(Path(raw_json).read_text(encoding="utf-8"))
    rows = []
    for item in raw["items"]:
        rows.append({
            "block_id": raw["block"],
            "item": item["item"],
            "elapsed_ms": item["elapsed_ms"],
            "ops_sec": item["ops_sec"],
            "p99_ms": item["p99_ms"],
            "rows_returned": item["rows_returned"],
            "result_hash": item["result_hash"],
            "timeout": item["timeout"],
            "error": item["error"],
        })
    csv_path = Path(csv_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(rows)
    frame.to_csv(csv_path, mode="a", header=not csv_path.exists(), index=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["pilot", "full"], required=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    cfg = yaml.safe_load(Path("bench/config.yaml").read_text(encoding="utf-8"))
    schedule = build_schedule(cfg, args.phase)
    out_dir = Path("data/raw") / args.phase
    blocks = pending(schedule, out_dir) if args.resume else schedule
    if args.dry_run:
        for block in blocks:
            print(f"DRY-RUN {block.block_id}")
        return
    preflight(cfg)
    for block in blocks:
        execute_block(block, cfg, out_dir)


if __name__ == "__main__":
    main()
