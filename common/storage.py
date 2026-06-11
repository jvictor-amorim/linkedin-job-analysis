#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
common.storage

Camada de persistência que honra a env STORAGE_BACKEND:

  local    -> grava data/jobs.csv e data/job_skills.csv (espelham as tabelas)
  database -> faz upsert no PostgreSQL (tabelas jobs e job_skills)

A entrada é a forma normalizada relacional:
  jobs_rows   = [{job_id, title, company, city, work_mode}, ...]
  skills_rows = [(job_id, skill), ...]
"""

import csv

from common import config

JOBS_CSV = config.DATA_DIR / "jobs.csv"
JOB_SKILLS_CSV = config.DATA_DIR / "job_skills.csv"


def _persist_local(jobs_rows: list, skills_rows: list) -> None:
    with JOBS_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["job_id", "title", "company", "city", "work_mode"]
        )
        writer.writeheader()
        for row in jobs_rows:
            writer.writerow({k: row.get(k) for k in writer.fieldnames})

    with JOB_SKILLS_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["job_id", "skill"])
        writer.writerows(skills_rows)

    print(
        f"[storage:local] {len(jobs_rows)} vagas -> {JOBS_CSV.name}, "
        f"{len(skills_rows)} skills -> {JOB_SKILLS_CSV.name}",
        flush=True,
    )


def _persist_database(jobs_rows: list, skills_rows: list) -> None:
    from common import db

    skills_by_job: dict = {}
    for job_id, skill in skills_rows:
        skills_by_job.setdefault(job_id, []).append(skill)

    conn = db.get_connection()
    try:
        db.ensure_schema(conn)
        for row in jobs_rows:
            db.upsert_job(conn, row)
            db.replace_job_skills(conn, row["job_id"], skills_by_job.get(row["job_id"], []))
        conn.commit()
    finally:
        conn.close()

    print(
        f"[storage:database] {len(jobs_rows)} vagas e {len(skills_rows)} skills "
        f"persistidas em {config.DB_NAME}@{config.DB_HOST}:{config.DB_PORT}",
        flush=True,
    )


def persist(jobs_rows: list, skills_rows: list) -> None:
    """Despacha para o backend escolhido em STORAGE_BACKEND."""
    if config.STORAGE_BACKEND == "database":
        _persist_database(jobs_rows, skills_rows)
    else:
        _persist_local(jobs_rows, skills_rows)
