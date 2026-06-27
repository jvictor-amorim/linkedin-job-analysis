#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
common.html_store

Cache do HTML bruto das vagas (job_id -> html_text), honrando STORAGE_BACKEND:

  local    -> data/job_html.csv   (colunas: job_id, html_text)
  database -> tabela job_html no Postgres

Serve para reprocessar as vagas sem refazer a request ao LinkedIn.
"""

import csv
import re
import sys

from common import config

HTML_CSV = config.DATA_DIR / "job_html.csv"

# O HTML inteiro pode estourar o limite padrão de campo do parser de CSV.
try:
    csv.field_size_limit(sys.maxsize)
except OverflowError:
    csv.field_size_limit(2**31 - 1)

_conn = None


def _db_conn():
    """Conexão psycopg2 reaproveitada + schema garantido (modo database)."""
    global _conn
    if _conn is None:
        from common import db

        _conn = db.get_connection()
        db.ensure_schema(_conn)
    return _conn


def load_html_map() -> dict:
    """Retorna {job_id: html_text} do cache. Vazio se não houver nada salvo."""
    if config.STORAGE_BACKEND == "database":
        conn = _db_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT job_id, html_text FROM job_html")
            return {str(jid): html for jid, html in cur.fetchall()}

    rows = {}
    if HTML_CSV.exists():
        with HTML_CSV.open("r", encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                jid = (row.get("job_id") or "").strip()
                if jid:
                    rows[jid] = row.get("html_text", "")
    return rows


def save_html(job_id: str, html_text: str) -> None:
    """Persiste (idempotente) o HTML bruto de uma vaga."""
    if config.STORAGE_BACKEND == "database":
        conn = _db_conn()
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO job_html (job_id, html_text)
                VALUES (%s, %s)
                ON CONFLICT (job_id) DO UPDATE SET
                    html_text  = EXCLUDED.html_text,
                    fetched_at = now()
                """,
                (str(job_id), html_text),
            )
        conn.commit()
        return

    # local: uma linha por vaga; remove quebras p/ não quebrar o CSV.
    HTML_CSV.parent.mkdir(parents=True, exist_ok=True)
    new_file = not HTML_CSV.exists()
    clean = re.sub(r"[\r\n]+", " ", html_text)
    with HTML_CSV.open("a", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, quoting=csv.QUOTE_ALL, lineterminator="\n")
        if new_file:
            writer.writerow(["job_id", "html_text"])
        writer.writerow([str(job_id), clean])
