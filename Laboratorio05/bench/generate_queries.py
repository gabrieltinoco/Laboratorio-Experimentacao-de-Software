import re
from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parent
DUCKDB_DIR = ROOT / "queries" / "duckdb"
SQLITE_DIR = ROOT / "queries" / "sqlite"


def translate(sql: str) -> str:
    sql = re.sub(
        r"date '([^']*)' \+ interval '(-?[0-9]+)' day",
        r"date('\1','+\2 day')",
        sql,
        flags=re.I,
    )
    sql = re.sub(
        r"extract\(year from ([^)]+)\)",
        r"CAST(strftime('%Y', \1) AS INTEGER)",
        sql,
        flags=re.I,
    )
    sql = re.sub(
        r"substring\(([^ ]+) from ([0-9]+) for ([0-9]+)\)",
        r"substr(\1, \2, \3)",
        sql,
        flags=re.I,
    )
    sql = re.sub(r"::[a-zA-Z]+", "", sql)
    sql = re.sub(r"CAST\('([^']*)' AS date\)", r"'\1'", sql, flags=re.I)
    sql = re.sub(r"date '([^']*)'", r"'\1'", sql, flags=re.I)
    sql = re.sub(
        r"\) AS c_orders \([^)]+\)",
        r") AS c_orders",
        sql,
        flags=re.I,
    )
    sql = re.sub(
        r"(count\(o_orderkey\))(?!\s+AS)",
        r"\1 AS c_count",
        sql,
        flags=re.I,
    )
    return sql


def main() -> None:
    DUCKDB_DIR.mkdir(parents=True, exist_ok=True)
    SQLITE_DIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute("INSTALL tpch")
    con.execute("LOAD tpch")
    rows = con.execute(
        "SELECT query_nr, query FROM tpch_queries() ORDER BY query_nr"
    ).fetchall()
    con.close()

    for number, query in rows:
        qid = f"q{number:02d}"
        (DUCKDB_DIR / f"{qid}.sql").write_text(
            "-- DuckDB TPC-H query; source: tpch_queries()\n" + query.strip() + "\n",
            encoding="utf-8",
        )
        (SQLITE_DIR / f"{qid}.sql").write_text(
            "-- SQLite translation: date interval -> date(); extract(year) -> strftime(); "
            "substring -> substr(); removed :: casts\n" + translate(query).strip() + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
