import time
import threading
from pathlib import Path

import apsw
import duckdb
import psutil

from bench import load_query
from bench.oltp import run_oltp
from bench.result_hash import result_hash


def run_block(block, cfg: dict) -> dict:
    engine_kind = cfg["engines"][block.engine]["kind"]
    if block.workload == "oltp":
        db_path = Path("data/db") / f"{block.block_id}.{ 'duckdb' if engine_kind == 'duckdb' else 'sqlite' }"
    else:
        db_path = Path("data/db") / f"tpch_sf{block.sf}.{ 'duckdb' if engine_kind == 'duckdb' else 'sqlite' }"
    items = []
    timeout_ms = int(cfg["timeout_ms"])
    process = psutil.Process()

    if engine_kind == "duckdb":
        conn = duckdb.connect(str(db_path), read_only=(block.workload == "olap"))
        if "threads" in cfg["engines"][block.engine]:
            conn.execute(f"SET threads={cfg['engines'][block.engine]['threads']}")
        conn.execute("SET memory_limit=?", [cfg["duckdb_settings"]["memory_limit"]])
    else:
        conn = apsw.Connection(str(db_path))
        conn.cursor().execute("PRAGMA journal_mode=WAL")
        conn.cursor().execute("PRAGMA synchronous=NORMAL")
        conn.cursor().execute("PRAGMA cache_size=-262144")

    try:
        for table in ("customer", "lineitem", "nation", "orders", "part", "partsupp", "region", "supplier"):
            if engine_kind == "duckdb":
                conn.execute(f"SELECT COUNT(*) FROM {table}")
            else:
                conn.cursor().execute(f"SELECT COUNT(*) FROM {table}")

        for item in __import__("bench.schedule", fromlist=["items_for"]).items_for(block, cfg):
            timeout = False
            error = ""
            elapsed_ms = 0.0
            ops_sec = float("nan")
            p99_ms = float("nan")
            rows_returned = 0
            hash_value = ""

            start = time.perf_counter_ns()
            watchdog = None
            try:
                if block.workload == "oltp":
                    result = run_oltp(
                        conn,
                        engine_kind,
                        item,
                        cfg["workloads"]["oltp"]["n_ops"],
                        cfg["seed"],
                    )
                    elapsed_ms = result["elapsed_ms"]
                    ops_sec = result["ops_sec"]
                    p99_ms = result["p99_ms"]
                else:
                    def interrupt():
                        conn.interrupt()

                    watchdog = threading.Timer(timeout_ms / 1000, interrupt)
                    watchdog.start()
                    sql = load_query(engine_kind, item)
                    if engine_kind == "duckdb":
                        rows = conn.execute(sql).fetchall()
                        elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000
                        rows_returned = len(rows)
                        hash_value = result_hash(rows)
                    else:
                        cursor = conn.cursor()
                        rows = cursor.execute(sql).fetchall()
                        elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000
                        rows_returned = len(rows)
                        hash_value = result_hash([tuple(row) for row in rows])
            except Exception as exc:
                error = str(exc)
                elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000
                if elapsed_ms >= timeout_ms * 0.8:
                    timeout = True
            finally:
                if watchdog is not None:
                    watchdog.cancel()

            items.append({
                "item": item,
                "elapsed_ms": elapsed_ms,
                "ops_sec": ops_sec,
                "p99_ms": p99_ms,
                "rows_returned": rows_returned,
                "result_hash": hash_value,
                "timeout": timeout,
                "error": error,
            })
    finally:
        conn.close()

    return {
        "block": block.block_id,
        "env": {
            "engine_version": duckdb.__version__ if engine_kind == "duckdb" else apsw.sqlitelibversion()
        },
        "items": items,
        "complete": True,
        "peak_rss_mb": process.memory_info().rss / (1024 * 1024),
    }
