from bench.datagen import generate, table_counts, SQLITE_INDEXES
import apsw


def test_generate_creates_both(tmp_path):
    duckdb_path, sqlite_path = generate(0.01, tmp_path)
    assert duckdb_path.exists()
    assert sqlite_path.exists()


def test_counts_match_across_engines(tmp_path):
    duckdb_path, sqlite_path = generate(0.01, tmp_path)
    assert table_counts(duckdb_path) == table_counts(sqlite_path)


def test_fixed_counts(tmp_path):
    _, sqlite_path = generate(0.01, tmp_path)
    counts = table_counts(sqlite_path)
    assert counts["nation"] == 25
    assert counts["region"] == 5
    assert counts["orders"] == 15000


def test_sqlite_has_indexes(tmp_path):
    _, sqlite_path = generate(0.01, tmp_path)
    conn = apsw.Connection(str(sqlite_path))
    rows = conn.cursor().execute("PRAGMA index_list('lineitem')").fetchall()
    conn.close()
    assert rows


def test_generate_idempotent(tmp_path):
    _, sqlite_path = generate(0.01, tmp_path)
    first_mtime = sqlite_path.stat().st_mtime_ns
    generate(0.01, tmp_path)
    assert sqlite_path.stat().st_mtime_ns == first_mtime
