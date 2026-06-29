from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_DB = Path("memory/agentic_memory.sqlite")
SCHEMA_VERSION = 1


SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS memories (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL CHECK (kind IN ('recipe', 'decision', 'pitfall', 'run_log')),
  title TEXT NOT NULL,
  summary TEXT NOT NULL,
  body_json TEXT NOT NULL,
  source_refs_json TEXT NOT NULL DEFAULT '[]',
  status TEXT NOT NULL DEFAULT 'active',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(
  id UNINDEXED,
  kind,
  title,
  summary,
  body
);
"""


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.execute(
        "INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)",
        ("schema_version", str(SCHEMA_VERSION)),
    )
    conn.commit()


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON file: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"Expected a JSON object: {path}")
    return data


def require_fields(data: dict[str, Any], fields: list[str], path: Path) -> None:
    missing = [field for field in fields if not data.get(field)]
    if missing:
        raise SystemExit(f"{path} is missing required fields: {', '.join(missing)}")


def compact_for_fts(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True)


def upsert_memory(conn: sqlite3.Connection, data: dict[str, Any]) -> None:
    memory_id = str(data["id"]).strip()
    kind = str(data["kind"]).strip()
    title = str(data["title"]).strip()
    summary = str(data["summary"]).strip()
    status = str(data.get("status", "active")).strip() or "active"
    source_refs = data.get("source_refs", [])
    if not isinstance(source_refs, list):
        raise SystemExit("source_refs must be a list")
    stamp = now_iso()
    previous = conn.execute("SELECT created_at FROM memories WHERE id = ?", (memory_id,)).fetchone()
    created_at = previous["created_at"] if previous else stamp
    body_json = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)
    source_refs_json = json.dumps(source_refs, ensure_ascii=False, sort_keys=True)
    conn.execute(
        """
        INSERT OR REPLACE INTO memories
          (id, kind, title, summary, body_json, source_refs_json, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (memory_id, kind, title, summary, body_json, source_refs_json, status, created_at, stamp),
    )
    conn.execute("DELETE FROM memory_fts WHERE id = ?", (memory_id,))
    conn.execute(
        "INSERT INTO memory_fts(id, kind, title, summary, body) VALUES (?, ?, ?, ?, ?)",
        (memory_id, kind, title, summary, compact_for_fts(data)),
    )
    conn.commit()


def add_recipe(conn: sqlite3.Connection, path: Path) -> None:
    data = load_json(path)
    require_fields(data, ["id", "title", "summary", "steps", "validation"], path)
    data["kind"] = "recipe"
    upsert_memory(conn, data)
    print(f"stored recipe: {data['id']}")


def add_run_log(conn: sqlite3.Connection, path: Path) -> None:
    data = load_json(path)
    require_fields(data, ["id", "title", "summary", "recipe_id", "result"], path)
    data["kind"] = "run_log"
    upsert_memory(conn, data)
    print(f"stored run_log: {data['id']}")


def get_memory(conn: sqlite3.Connection, memory_id: str) -> int:
    row = conn.execute("SELECT body_json FROM memories WHERE id = ?", (memory_id,)).fetchone()
    if not row:
        print(f"not found: {memory_id}", file=sys.stderr)
        return 1
    print(row["body_json"])
    return 0


def search(conn: sqlite3.Connection, query: str, kind: str | None, limit: int) -> None:
    sql = """
        SELECT m.id, m.kind, m.title, m.summary, m.updated_at
        FROM memory_fts f
        JOIN memories m ON m.id = f.id
        WHERE memory_fts MATCH ?
    """
    params: list[Any] = [query]
    if kind:
        sql += " AND m.kind = ?"
        params.append(kind)
    sql += " ORDER BY rank LIMIT ?"
    params.append(limit)
    rows = conn.execute(sql, params).fetchall()
    json.dump([dict(row) for row in rows], sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


def list_memories(conn: sqlite3.Connection, kind: str | None) -> None:
    sql = "SELECT id, kind, title, summary, status, updated_at FROM memories"
    params: list[Any] = []
    if kind:
        sql += " WHERE kind = ?"
        params.append(kind)
    sql += " ORDER BY updated_at DESC"
    rows = conn.execute(sql, params).fetchall()
    json.dump([dict(row) for row in rows], sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Store compact agentic memory recipes and run logs.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="SQLite memory database path.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init", help="Create or migrate the local memory database.")

    recipe = sub.add_parser("add-recipe", help="Add or update a procedural memory recipe from JSON.")
    recipe.add_argument("path", type=Path)

    run_log = sub.add_parser("add-run-log", help="Add a compact execution memory from JSON.")
    run_log.add_argument("path", type=Path)

    get = sub.add_parser("get", help="Print one memory object by id.")
    get.add_argument("id")

    search_cmd = sub.add_parser("search", help="Search compact memories with SQLite FTS5.")
    search_cmd.add_argument("query")
    search_cmd.add_argument("--kind", choices=["recipe", "decision", "pitfall", "run_log"])
    search_cmd.add_argument("--limit", type=int, default=5)

    list_cmd = sub.add_parser("list", help="List memories.")
    list_cmd.add_argument("--kind", choices=["recipe", "decision", "pitfall", "run_log"])
    return parser


def main() -> int:
    args = build_parser().parse_args()
    with connect(args.db) as conn:
        init_db(conn)
        if args.command == "init":
            print(f"initialized {args.db}")
            return 0
        if args.command == "add-recipe":
            add_recipe(conn, args.path)
            return 0
        if args.command == "add-run-log":
            add_run_log(conn, args.path)
            return 0
        if args.command == "get":
            return get_memory(conn, args.id)
        if args.command == "search":
            search(conn, args.query, args.kind, args.limit)
            return 0
        if args.command == "list":
            list_memories(conn, args.kind)
            return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
