#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
common.config

Configuração central do pipeline ETL: carrega o .env, expõe os caminhos de
dados/logs e as configurações de backend de armazenamento (local vs banco).

Importável de qualquer script do projeto desde que a raiz do repositório esteja
no sys.path (ver o bootstrap no topo de cada script movido).
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Raiz do repositório = pasta-pai de common/
BASE_DIR = Path(__file__).resolve().parent.parent

# Snapshot do ambiente do shell ANTES de carregar o .env, para que variáveis
# passadas explicitamente no comando (ex.: STORAGE_BACKEND=database python ...)
# tenham precedência sobre o .env nos toggles abaixo.
_shell_env = dict(os.environ)

# override=True permite alterar variáveis em runtime sem recriar o processo.
load_dotenv(BASE_DIR / ".env", override=True)


def _get(key: str, default: str | None = None) -> str | None:
    """Env do shell vence; senão o valor do .env; senão o default."""
    return _shell_env.get(key) or os.getenv(key, default)

# ---------------------------------------------------------------------------
# Caminhos
# ---------------------------------------------------------------------------
DATA_DIR = BASE_DIR / "data"
SQL_DIR = BASE_DIR / "sql"
SCHEMA_SQL = SQL_DIR / "schema.sql"

DATA_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# HTTP / scraping
# ---------------------------------------------------------------------------
REQUEST_DELAY_MIN = int(_get("REQUEST_DELAY_MIN", "5"))
REQUEST_DELAY_MAX = int(_get("REQUEST_DELAY_MAX", "15"))

# ---------------------------------------------------------------------------
# Backend de armazenamento
# ---------------------------------------------------------------------------
# "local"  -> grava CSV/JSON em data/
# "database" -> grava no PostgreSQL configurado abaixo
STORAGE_BACKEND = _get("STORAGE_BACKEND", "local").lower()

# Postgres (mesmas credenciais do docker-compose.yaml).
# No host use DB_HOST=localhost (porta exposta no compose);
# dentro do Airflow use DB_HOST=postgres.
DB_HOST = _get("DB_HOST", "localhost")
DB_PORT = int(_get("DB_PORT", "5432"))
DB_NAME = _get("DB_NAME", "airflow")
DB_USER = _get("DB_USER", "airflow")
DB_PASSWORD = _get("DB_PASSWORD", "airflow")
