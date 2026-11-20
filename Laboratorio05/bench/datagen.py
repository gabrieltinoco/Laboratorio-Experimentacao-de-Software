from pathlib import Path
import hashlib
import json

import apsw
import duckdb


SQLITE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS lineitem_l_orderkey_idx ON lineitem(l_orderkey)",
    "CREATE INDEX IF NOT EXISTS lineitem_l_partkey_idx ON lineitem(l_partkey)",
    "CREATE INDEX IF NOT EXISTS lineitem_l_suppkey_idx ON lineitem(l_suppkey)",
    "CREATE INDEX IF NOT EXISTS orders_o_custkey_idx ON orders(o_custkey)",
    "CREATE INDEX IF NOT EXISTS partsupp_ps_partkey_idx ON partsupp(ps_partkey)",
    "CREATE INDEX IF NOT EXISTS partsupp_ps_suppkey_idx ON partsupp(ps_suppkey)",
    "CREATE INDEX IF NOT EXISTS customer_c_nationkey_idx ON customer(c_nationkey)",
    "CREATE INDEX IF NOT EXISTS supplier_s_nationkey_idx ON supplier(s_nationkey)",
    "CREATE INDEX IF NOT EXISTS nation_n_regionkey_idx ON nation(n_regionkey)",
]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _manifest_matches(out_dir: Path, sf: float) -> bool:
    manifest = out_dir.parent / "manifest.json"
    if not manifest.exists():
        return False
    data = json.loads(manifest.read_text(encoding="utf-8"))
    stem = f"tpch_sf{sf}"
    hashes = data.get("files", {})
    duckdb_path = out_dir / f"{stem}.duckdb"
    sqlite_path = out_dir / f"{stem}.sqlite"
    return (
        duckdb_path.exists()
        and sqlite_path.exists()
        and hashes.get(duckdb_path.as_posix()) == _sha256(duckdb_path)
        and hashes.get(sqlite_path.as_posix()) == _sha256(sqlite_path)
    )


def generate(sf: float, out_dir: Path = Path("data/db")) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    duckdb_path = out_dir / f"tpch_sf{sf}.duckdb"
    sqlite_path = out_dir / f"tpch_sf{sf}.sqlite"

    if duckdb_path.exists() and sqlite_path.exists():
        return duckdb_path, sqlite_path

    for path in (duckdb_path, sqlite_path):
        if path.exists():
            path.unlink()

    con = duckdb.connect(str(duckdb_path))
    con.execute("INSTALL tpch")
    con.execute("LOAD tpch")
    con.execute("CALL dbgen(sf = ?)", [sf])

    con.execute("INSTALL sqlite")
    con.execute("LOAD sqlite")
    con.execute(
        f"ATTACH '{sqlite_path.as_posix()}' AS tpch_sqlite (TYPE sqlite)"
    )
    con.execute("CREATE SCHEMA IF NOT EXISTS tpch_sqlite.main")
    casts = {
        "customer": {"c_acctbal": "DOUBLE"},
        "lineitem": {
            "l_quantity": "DOUBLE",
            "l_extendedprice": "DOUBLE",
            "l_discount": "DOUBLE",
            "l_tax": "DOUBLE",
        },
        "orders": {"o_totalprice": "DOUBLE"},
        "part": {"p_retailprice": "DOUBLE"},
        "partsupp": {"ps_supplycost": "DOUBLE", "ps_availqty": "DOUBLE"},
    }
    for table in ("customer", "lineitem", "nation", "orders", "part", "partsupp", "region", "supplier"):
        columns = con.execute(f"DESCRIBE {table}").fetchall()
        expressions = []
        table_casts = casts.get(table, {})
        for column in columns:
            name = column[0]
            if name in table_casts:
                expressions.append(f"CAST({name} AS DOUBLE) AS {name}")
            elif table == "lineitem" and name.startswith("l_") and name.endswith("date"):
                expressions.append(f"CAST({name} AS VARCHAR) AS {name}")
            elif table == "orders" and name.startswith("o_") and name.endswith("date"):
                expressions.append(f"CAST({name} AS VARCHAR) AS {name}")
            else:
                expressions.append(name)
        con.execute(
            f"""
            CREATE TABLE tpch_sqlite.main.{table} AS
            SELECT {', '.join(expressions)} FROM {table}
            """
        )
    con.close()

    conn = apsw.Connection(str(sqlite_path))
    conn.cursor().execute("PRAGMA journal_mode=WAL")
    conn.cursor().execute("PRAGMA synchronous=NORMAL")
    conn.cursor().execute("PRAGMA cache_size=-262144")
    for statement in SQLITE_INDEXES:
        conn.cursor().execute(statement)
    conn.cursor().execute("ANALYZE")
    conn.close()

    return duckdb_path, sqlite_path


def table_counts(db: Path) -> dict[str, int]:
    db = Path(db)
    counts: dict[str, int] = {}
    tables = ("customer", "lineitem", "nation", "orders", "part", "partsupp", "region", "supplier")
    if db.suffix == ".sqlite":
        conn = apsw.Connection(str(db))
        for table in tables:
            row = conn.cursor().execute(f"SELECT COUNT(*) FROM {table}").fetchone()
            counts[table] = int(row[0])
        conn.close()
    else:
        con = duckdb.connect(str(db), read_only=True)
        for table in tables:
            counts[table] = int(con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
        con.close()
    return counts
