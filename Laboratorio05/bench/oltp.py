import random
import time
from typing import Literal


def run_oltp(conn, kind: str, op: Literal["point_select", "insert", "update"], n_ops: int, seed: int) -> dict:
    rng = random.Random(seed)
    latencies_ns = []
    start = time.perf_counter_ns()

    if kind == "duckdb":
        if op == "insert":
            conn.execute("DROP TABLE IF EXISTS orders_bench")
            conn.execute("CREATE TABLE orders_bench AS SELECT * FROM orders WHERE FALSE")
        for _ in range(n_ops):
            key = rng.randint(1, 1500000)
            operation_start = time.perf_counter_ns()
            if op == "point_select":
                conn.execute("SELECT * FROM orders WHERE o_orderkey = ?", [key]).fetchone()
            elif op == "insert":
                conn.execute(
                    "INSERT INTO orders_bench (o_orderkey, o_custkey, o_orderstatus, o_totalprice, o_orderdate, o_orderpriority, o_clerk, o_shippriority, o_comment) "
                    "VALUES (?, 1, 'O', 0.0, DATE '1995-01-01', '1-URGENT', 'Clerk#000000001', 0, 'benchmark')",
                    [key + 10_000_000],
                )
            else:
                conn.execute("UPDATE orders SET o_comment = 'benchmark' WHERE o_orderkey = ?", [key])
            latencies_ns.append(time.perf_counter_ns() - operation_start)
    else:
        cursor = conn.cursor()
        if op == "insert":
            cursor.execute("DROP TABLE IF EXISTS orders_bench")
            cursor.execute("CREATE TABLE orders_bench AS SELECT * FROM orders WHERE 0")
        for _ in range(n_ops):
            key = rng.randint(1, 1500000)
            operation_start = time.perf_counter_ns()
            if op == "point_select":
                cursor.execute("SELECT * FROM orders WHERE o_orderkey = ?", (key,))
                cursor.fetchone()
            elif op == "insert":
                cursor.execute(
                    "INSERT INTO orders_bench (o_orderkey, o_custkey, o_orderstatus, o_totalprice, o_orderdate, o_orderpriority, o_clerk, o_shippriority, o_comment) "
                    "VALUES (?, 1, 'O', 0.0, '1995-01-01', '1-URGENT', 'Clerk#000000001', 0, 'benchmark')",
                    (key + 10_000_000,),
                )
            else:
                cursor.execute("UPDATE orders SET o_comment = 'benchmark' WHERE o_orderkey = ?", (key,))
            latencies_ns.append(time.perf_counter_ns() - operation_start)

    elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000
    ordered = sorted(latencies_ns)
    p99_index = max(0, int(len(ordered) * 0.99) - 1)
    p99_ms = ordered[p99_index] / 1_000_000
    return {"elapsed_ms": elapsed_ms, "ops_sec": n_ops / (elapsed_ms / 1000), "p99_ms": p99_ms}
