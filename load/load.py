#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
load.py — etapa LOAD do pipeline.

Lê a saída da abordagem de scraping (data/scrape_html_rule.json), normaliza
em linhas relacionais (jobs + job_skills) e persiste via common.storage, que
escolhe o destino conforme a env STORAGE_BACKEND:

  STORAGE_BACKEND=local     -> data/jobs.csv + data/job_skills.csv
  STORAGE_BACKEND=database  -> PostgreSQL (tabelas jobs e job_skills)
"""

import json
import sys
from pathlib import Path

# Bootstrap: sobe até achar o pacote `common` e o coloca no sys.path.
_root = Path(__file__).resolve()
while not (_root / "common").is_dir():
    _root = _root.parent
sys.path.insert(0, str(_root))

from common import config, storage

INPUT_JSON = config.DATA_DIR / "scrape_html_rule.json"


def load_entries() -> list:
    if not INPUT_JSON.exists():
        print(f"Arquivo de entrada não encontrado: {INPUT_JSON}", flush=True)
        return []
    content = INPUT_JSON.read_text(encoding="utf-8").strip()
    return json.loads(content) if content else []


def normalize(entries: list) -> tuple[list, list]:
    """Separa as entradas em (jobs_rows, skills_rows)."""
    jobs_rows = []
    skills_rows = []
    for e in entries:
        job_id = e.get("job_id")
        if not job_id:
            continue
        jobs_rows.append(
            {
                "job_id": job_id,
                "title": e.get("title"),
                "company": e.get("company"),
                "city": e.get("city"),
                "work_mode": e.get("work_mode"),
            }
        )
        for skill in e.get("skills", []):
            skills_rows.append((job_id, skill))
    return jobs_rows, skills_rows


def main() -> None:
    entries = load_entries()
    if not entries:
        print("Nada para carregar.", flush=True)
        return

    jobs_rows, skills_rows = normalize(entries)
    print(
        f"Destino: STORAGE_BACKEND={config.STORAGE_BACKEND} | "
        f"{len(jobs_rows)} vagas, {len(skills_rows)} skills",
        flush=True,
    )
    storage.persist(jobs_rows, skills_rows)
    print("Load concluído.", flush=True)


if __name__ == "__main__":
    main()
