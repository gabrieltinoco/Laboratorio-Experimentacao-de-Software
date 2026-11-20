import pytest
import duckdb
import apsw

from bench import load_query
from bench.datagen import generate
from bench.result_hash import result_hash


def test_all_queries_present():
    for kind in ("duckdb", "sqlite"):
        assert all(load_query(kind, f"q{number:02d}") for number in range(1, 23))


@pytest.mark.parametrize("number", range(1, 23))
def test_results_match_across_engines(tmp_path, number):
    duckdb_path, sqlite_path = generate(0.01, tmp_path)
    sql_duckdb = load_query("duckdb", f"q{number:02d}")
    sql_sqlite = load_query("sqlite", f"q{number:02d}")
    con = duckdb.connect(str(duckdb_path), read_only=True)
    duck_rows = con.execute(sql_duckdb).fetchall()
    con.close()
    conn = apsw.Connection(str(sqlite_path))
    sqlite_rows = conn.cursor().execute(sql_sqlite).fetchall()
    conn.close()
    assert result_hash(duck_rows) == result_hash(sqlite_rows)
