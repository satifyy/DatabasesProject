"""Utility helpers for provisioning the curriculum tracking schema."""

from __future__ import annotations

import argparse
import configparser
import pathlib
import sys
from typing import Iterable

import mysql.connector

ROOT = pathlib.Path(__file__).resolve().parent
SCHEMA_FILE = ROOT / "schema.sql"
DATA_FILE = ROOT / "sample_data.sql"
CONFIG_FILE = ROOT / "config.ini"


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(
            "config.ini not found – copy config.ini.example or edit existing one."
        )
    parser = configparser.ConfigParser()
    parser.read(CONFIG_FILE)
    if "database" not in parser:
        raise KeyError("[database] section missing from config.ini")
    cfg = parser["database"]
    return dict(
        host=cfg.get("host", "localhost"),
        port=cfg.getint("port", 3306),
        user=cfg.get("user"),
        password=cfg.get("password"),
        database=cfg.get("database"),
        charset="utf8mb4",
    )


def connect() -> mysql.connector.MySQLConnection:
    cfg = load_config()
    conn = mysql.connector.connect(
        host=cfg["host"],
        port=cfg["port"],
        user=cfg["user"],
        password=cfg["password"],
        autocommit=False,
    )
    cur = conn.cursor()
    cur.execute("CREATE DATABASE IF NOT EXISTS {}".format(cfg["database"]))
    cur.execute("USE `{}`".format(cfg["database"]))
    cur.close()
    conn.database = cfg["database"]
    return conn


def execute_statements(cur, statements: Iterable[str]):
    for stmt in statements:
        sql = stmt.strip()
        if sql:
            cur.execute(sql)


def read_sql_file(path: pathlib.Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"Missing SQL file: {path}")
    content = path.read_text(encoding="utf-8")
    # naive split is fine here because the schema files avoid procedures
    parts = [chunk for chunk in content.split(";") if chunk.strip()]
    return [part + ";" for part in parts]


def apply_schema() -> None:
    with connect() as conn:
        cur = conn.cursor()
        statements = read_sql_file(SCHEMA_FILE)
        execute_statements(cur, statements)
        conn.commit()
        cur.close()


def load_sample_data() -> None:
    with connect() as conn:
        cur = conn.cursor()
        statements = read_sql_file(DATA_FILE)
        execute_statements(cur, statements)
        conn.commit()
        cur.close()


def reset_database(confirm: bool) -> None:
    if not confirm:
        print("Pass --yes to confirm dropping all data.")
        return
    cfg = load_config()
    with mysql.connector.connect(
        host=cfg["host"],
        port=cfg["port"],
        user=cfg["user"],
        password=cfg["password"],
        autocommit=True,
    ) as conn:
        cur = conn.cursor()
        cur.execute("DROP DATABASE IF EXISTS `{}`".format(cfg["database"]))
        cur.close()
    print("Database dropped. Re-run --init to recreate schema.")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Provision the degree evaluation schema and seed data."
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help="Create the schema defined in schema.sql",
    )
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Load the sample dataset from sample_data.sql",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop the configured database (requires --yes)",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Confirm destructive operations (used with --reset)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv or sys.argv[1:])
    if not any((args.init, args.seed, args.reset)):
        print("No action specified. Use --init, --seed, or --reset.")
        return
    if args.reset:
        reset_database(args.yes)
    if args.init:
        apply_schema()
        print("Schema applied.")
    if args.seed:
        load_sample_data()
        print("Sample data loaded.")


if __name__ == "__main__":
    main()
