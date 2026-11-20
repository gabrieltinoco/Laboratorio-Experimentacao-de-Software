import json
import platform
import shutil
from pathlib import Path

import psutil
import duckdb
import apsw


def snapshot(out: Path = Path("data/raw/env.json")) -> dict:
    disk = shutil.disk_usage(Path.cwd())
    value = {
        "host_id": platform.node(),
        "platform": platform.platform(),
        "cpu_count": psutil.cpu_count(logical=True),
        "mem_gb": round(psutil.virtual_memory().total / (1024 ** 3), 2),
        "free_disk_gb": round(disk.free / (1024 ** 3), 2),
        "duckdb": duckdb.__version__,
        "sqlite": apsw.sqlitelibversion(),
    }
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")
    return value
