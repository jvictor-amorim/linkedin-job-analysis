#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
common.db

Acesso ao PostgreSQL via psycopg2. Garante o schema (sql/schema.sql) e oferece
operações idempotentes de upsert de vagas e substituição de skills.
"""

import psycopg2

from common import config


def get_connection():
    """Abre uma conexão com o Postgres usando as credenciais de common.config."""
    return psycopg2.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        dbname=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
    )


def ensure_schema(conn) -> None:
    """Executa sql/schema.sql (idempotente: CREATE TABLE IF NOT EXISTS)."""
    ddl = config.SCHEMA_SQL.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(ddl)
    conn.commit()


def upsert_job(conn, row: dict) -> None:
    """Insere/atualiza uma vaga (chave: job_id)."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO jobs (job_id, title, company, city, work_mode)
            VALUES (%(job_id)s, %(title)s, %(company)s, %(city)s, %(work_mode)s)
            ON CONFLICT (job_id) DO UPDATE SET
                title     = EXCLUDED.title,
                company   = EXCLUDED.company,
                city      = EXCLUDED.city,
                work_mode = EXCLUDED.work_mode
            """,
            {
                "job_id": row.get("job_id"),
                "title": row.get("title"),
                "company": row.get("company"),
                "city": row.get("city"),
                "work_mode": row.get("work_mode"),
            },
        )


def replace_job_skills(conn, job_id: str, skills: list) -> None:
    """Substitui as skills de uma vaga (DELETE + INSERT), mantendo idempotência."""
    with conn.cursor() as cur:
        cur.execute("DELETE FROM job_skills WHERE job_id = %s", (job_id,))
        for skill in skills:
            cur.execute(
                """
                INSERT INTO job_skills (job_id, skill)
                VALUES (%s, %s)
                ON CONFLICT (job_id, skill) DO NOTHING
                """,
                (job_id, skill),
            )
