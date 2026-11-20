import apsw
import duckdb
import pytest

from bench.datagen import generate
from bench.oltp import run_oltp


@pytest.mark.parametrize("kind", ["duckdb", "sqlite"])
@pytest.mark.parametrize("op", ["point_select", "insert", "update"])
def test_oltp_returns_metrics(tmp_path, kind, op):
    duckdb_path, sqlite_path = generate(0.01, tmp_path)
    if kind == "duckdb":
        conn = duckdb.connect(str(duckdb_path))
    else:
        conn = apsw.Connection(str(sqlite_path))
    result = run_oltp(conn, kind, op, 100, 20262)
    conn.close()
    assert result["ops_sec"] > 0
    assert result["p99_ms"] >= 0


def test_oltp_insert_does_not_touch_orders(tmp_path):
    _, sqlite_path = generate(0.01, tmp_path)
    conn = apsw.Connection(str(sqlite_path))
    before = conn.cursor().execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    run_oltp(conn, "sqlite", "insert", 100, 20262)
    after = conn.cursor().execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    conn.close()
    assert after == before
