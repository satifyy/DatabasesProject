import configparser
from pathlib import Path
from typing import Any, Dict

import pymysql
from pymysql.cursors import DictCursor


_CONFIG_CACHE: Dict[str, Any] | None = None
CONFIG_PATH = Path(__file__).with_name("config.ini")


def _load_config() -> Dict[str, Any]:
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE
    parser = configparser.ConfigParser()
    if not parser.read(CONFIG_PATH):
        raise RuntimeError(f"Unable to read database configuration at {CONFIG_PATH}")
    if "database" not in parser:
        raise RuntimeError("Missing [database] section in config.ini")
    _CONFIG_CACHE = dict(parser["database"])
    return _CONFIG_CACHE


def create_connection() -> pymysql.connections.Connection:
    cfg = _load_config()
    return pymysql.connect(
        host=cfg.get("host", "localhost"),
        port=int(cfg.get("port", 3306)),
        user=cfg.get("user", ""),
        password=cfg.get("password", ""),
        database=cfg.get("database", ""),
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=True,
        init_command="SET sql_mode='STRICT_TRANS_TABLES'",
    )
