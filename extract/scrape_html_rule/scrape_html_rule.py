#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scrape_html_rule.py

Script de extração implementado.
Abordagem inteligente por dicionário de regex (sem classificação por seção).

Para cada job_id ainda não processado: obtém o HTML da vaga, aplica o motor de
regex de skills + detecção de modalidade e grava imediatamente o resultado:
    { job_id, title, company, city, work_mode, skills: [...] }

O destino segue STORAGE_BACKEND (ver common/config.py):
  database  grava direto nas tabelas jobs + job_skills (via common.db) e NÃO cria
            nenhum arquivo local; a idempotência vem da tabela jobs.
  local     grava em data/scrape_html_rule.json; a idempotência vem do próprio JSON.

As etapas são controladas por --stage:
  fetch              só BAIXA o HTML das vagas (de data/job_ids.csv) para o cache,
                     sem extrair nada — etapa de rede, isolável e lenta.
  extract            só EXTRAI do HTML já em cache (offline, sem rede) → destino.
  all      (padrão)  baixa o que faltar no cache e já extrai, numa passada só.

O cache de HTML (job_id, html_text) também segue STORAGE_BACKEND: data/job_html.csv
(local) ou tabela job_html (database) — ver common/html_store.py.

O dicionário de skills fica em skills_dict.py.
"""

import argparse
import csv
import json
import random
import re
import sys
import time
import unicodedata
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# Garante flush imediato para não perder linhas no terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

from bs4 import BeautifulSoup

# Bootstrap: sobe até achar o pacote `common` e o coloca no sys.path.
_root = Path(__file__).resolve()
while not (_root / "common").is_dir():
    _root = _root.parent
sys.path.insert(0, str(_root))

from common.config import DATA_DIR, REQUEST_DELAY_MIN, REQUEST_DELAY_MAX
from common import config, html_store

from skills_dict import SKILLS

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
JOB_IDS_CSV = DATA_DIR / "job_ids.csv"
OUTPUT_JSON = DATA_DIR / "scrape_html_rule.json"

DETAIL_URL = "https://br.linkedin.com/jobs-guest/jobs/api/jobPosting/{}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def _random_delay() -> float:
    return random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)


# ===========================================================================
# MOTOR DE REGEX DE SKILLS
# ===========================================================================
def _norm(s: str) -> str:
    """Remove acentos, baixa caixa, colapsa espaços. Garante matching estável."""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", s).lower()


def _alias_body(alias: str) -> str | None:
    """Corpo de regex de um alias, tolerando junto/separado/hífen/barra.
    Ex.: 'data integration' -> casa 'data integration', 'dataintegration',
    'data-integration'. Funciona com tokens que têm dígitos/símbolos como
    's3', 'ci/cd', 'k8s'. Retorna só o corpo (sem âncoras)."""
    a = _norm(alias).strip()
    tokens = [re.escape(t) for t in re.split(r"[\s/\-]+", a) if t]
    if not tokens:
        return None
    return r"[\s\-/]*".join(tokens)


def _build_engine():
    """Monta UM único regex com todos os aliases ordenados do mais longo para o
    mais curto (longest-match). Usar um padrão unificado + finditer faz o trecho
    casado ser consumido sem overlap: 'spark sql' casa 'Spark SQL' e o 'spark'
    interno NÃO dispara de novo. Roda uma vez na importação.

    Retorna (regex_compilado, dict chave-normalizada -> nome canônico)."""
    pairs = sorted(
        ((alias, canon) for canon, aliases in SKILLS.items() for alias in aliases),
        key=lambda x: len(_norm(x[0])),
        reverse=True,
    )
    parts: list[str] = []
    lookup: dict[str, str] = {}
    for alias, canon in pairs:
        body = _alias_body(alias)
        if not body:
            continue
        parts.append(body)
        # chave: alias normalizado com separadores colapsados, p/ resolver o match
        lookup[re.sub(r"[\s\-/]+", "", _norm(alias))] = canon
    pattern = re.compile(
        r"(?<![a-z0-9])(?:" + "|".join(parts) + r")(?![a-z0-9])", re.I
    )
    return pattern, lookup


# pré-compila uma vez
_MASTER, _LOOKUP = _build_engine()


def extract_skills(text: str) -> list[str]:
    """Retorna a lista de skills canônicas encontradas no texto, ordenada.
    Cada nome canônico entra no máximo uma vez. Longest-match garante que
    aliases compostos (ex.: 'spark sql') vençam o alias curto contido neles."""
    if not text:
        return []
    norm = _norm(text)
    found = set()
    for m in _MASTER.finditer(norm):
        key = re.sub(r"[\s\-/]+", "", m.group(0).lower())
        canon = _LOOKUP.get(key)
        if canon:
            found.add(canon)
    return sorted(found)


# ===========================================================================
# MODALIDADE DE TRABALHO (presencial / remoto / hibrido)
# ===========================================================================
_RE_HIBRIDO = re.compile(r"\bhibrido\b|\bhybrid\b")
_RE_REMOTO = re.compile(r"\bremoto\b|\bremote\b|home\s*office|100%\s*remoto|trabalho remoto|anywhere")
_RE_PRESENCIAL = re.compile(r"\bpresencial\b|on[\s\-]?site|\bno local\b|\bpresential\b")


def detect_modalidade(*partes: str) -> str | None:
    """Detecta a modalidade de trabalho a partir de cargo/cidade/descrição.

    Regras (nessa ordem): palavra-chave explícita de híbrido vence; se houver
    sinais de remoto E presencial juntos, classifica como híbrido; senão usa o
    que aparecer. Retorna None se nada casar."""
    texto = _norm(" ".join(p for p in partes if p))
    if not texto:
        return None
    tem_remoto = bool(_RE_REMOTO.search(texto))
    tem_presencial = bool(_RE_PRESENCIAL.search(texto))
    if _RE_HIBRIDO.search(texto) or (tem_remoto and tem_presencial):
        return "hibrido"
    if tem_remoto:
        return "remoto"
    if tem_presencial:
        return "presencial"
    return None


# ===========================================================================
# PARSERS DE HTML
# ===========================================================================
def parse_markup_text(html: str) -> str:
    """Texto bruto do container .show-more-less-html__markup (innerText-like)."""
    soup = BeautifulSoup(html, "html.parser")
    container = soup.select_one(".show-more-less-html__markup")
    if container is None:
        return ""
    return container.get_text("\n").strip()


def parse_job_meta(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    cargo_el = soup.select_one("h2.top-card-layout__title.topcard__title")
    cargo = cargo_el.get_text(strip=True) if cargo_el else None

    empresa = None
    empresa_el = soup.select_one("img[data-ghost-classes='artdeco-entity-image--ghost']")
    if empresa_el and empresa_el.get("alt"):
        empresa = empresa_el["alt"].strip()
    if not empresa:
        org = soup.select_one("a.topcard__org-name-link")
        if org:
            empresa = org.get_text(strip=True)

    cidade = None
    cidade_el = soup.select_one(".topcard__flavor.topcard__flavor--bullet")
    if cidade_el:
        cidade = cidade_el.get_text(strip=True)

    return {"title": cargo, "company": empresa, "city": cidade}


# ===========================================================================
# HTTP
# ===========================================================================
def fetch_html(url: str) -> str:
    req = Request(url, headers=HEADERS)
    try:
        with urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except (HTTPError, URLError) as exc:
        print(f"[WARN] Failed to fetch {url}: {exc}", file=sys.stderr)
        return ""


# ===========================================================================
# I/O — JSON de skills
# ===========================================================================
def load_output() -> list:
    if OUTPUT_JSON.exists():
        content = OUTPUT_JSON.read_text(encoding="utf-8").strip()
        if content:
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                pass
    return []


def save_output(data: list) -> None:
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_JSON.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)


def load_job_ids() -> list:
    if not JOB_IDS_CSV.exists():
        return []
    with JOB_IDS_CSV.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        return [row["job_id"] for row in reader if row.get("job_id")]


# ===========================================================================
# Montagem da entrada
# ===========================================================================
def build_entry(job_id: str, html: str) -> dict:
    """Monta a entrada de saída (title/company/city/work_mode/skills) a partir do HTML."""
    meta = parse_job_meta(html)
    descricao = parse_markup_text(html)
    skills = extract_skills(descricao)
    work_mode = detect_modalidade(meta["title"], meta["city"], descricao)
    return {
        "job_id": job_id,
        "title": meta["title"],
        "company": meta["company"],
        "city": meta["city"],
        "work_mode": work_mode,
        "skills": skills,
    }


# ===========================================================================
# Passada principal — obtém HTML (request/cache) + extrai + grava
# ===========================================================================
def _db_processed_ids(conn) -> set:
    """Conjunto de job_ids já gravados na tabela jobs (idempotência no modo database)."""
    with conn.cursor() as cur:
        cur.execute("SELECT job_id FROM jobs")
        return {str(r[0]) for r in cur.fetchall()}


def run(job_ids: list, allow_fetch: bool, html_cache: dict) -> None:
    """Etapa de extração: para cada vaga ainda não processada, obtém o HTML (do
    cache se houver; senão baixa, se allow_fetch), extrai skills/modalidade e grava
    no destino conforme STORAGE_BACKEND. Com allow_fetch=False, vagas sem HTML em
    cache são puladas (reprocessamento offline). Idempotente (vaga já gravada é
    pulada) e Ctrl-C é seguro (cada entrada é persistida imediatamente)."""
    use_db = config.STORAGE_BACKEND == "database"
    total = len(job_ids)

    if use_db:
        from common import db
        conn = db.get_connection()
        db.ensure_schema(conn)
        processed = _db_processed_ids(conn)
        output = None
    else:
        conn = None
        output = load_output()
        processed = {str(item["job_id"]) for item in output if item.get("job_id")}

    try:
        for idx, job_id in enumerate(job_ids, start=1):
            jid = str(job_id)
            if jid in processed:
                destino = "no banco" if use_db else "no JSON"
                print(f"[{idx}/{total}] {job_id} já {destino}, pulando", flush=True)
                continue

            downloaded = False
            if jid in html_cache:
                html = html_cache[jid]  # reusa cache, sem request
            elif not allow_fetch:
                print(f"[{idx}/{total}] {job_id} sem HTML no cache, pulando", flush=True)
                continue
            else:
                print(f"[{idx}/{total}] baixando {job_id} …", flush=True)
                html = fetch_html(DETAIL_URL.format(job_id))
                if not html:
                    print("  → resposta vazia, pulando.", flush=True)
                    continue
                html_store.save_html(job_id, html)  # salva no cache p/ reprocessar
                html_cache[jid] = html
                downloaded = True

            entry = build_entry(job_id, html)
            if use_db:
                db.upsert_job(conn, entry)
                db.replace_job_skills(conn, jid, entry["skills"])
                conn.commit()
            else:
                output.append(entry)
                save_output(output)
            processed.add(jid)
            _print_entry(entry, downloaded, len(processed))

            if downloaded:
                delay = _random_delay()
                print(f"  → aguardando {delay:.1f}s …", flush=True)
                time.sleep(delay)
    finally:
        if conn is not None:
            conn.close()


def _print_entry(entry: dict, downloaded: bool, count: int) -> None:
    cargo_str = entry["title"] or "(sem cargo)"
    empresa_str = entry["company"] or "(sem empresa)"
    cidade_str = entry["city"] or "(sem cidade)"
    skills = entry["skills"]
    origem = "baixado" if downloaded else "cache"
    print(
        f"  → [{origem}] {cargo_str} @ {empresa_str} ({cidade_str}) "
        f"→ {len(skills)} skills: {skills[:5]} [processadas: {count}]",
        flush=True,
    )


def run_fetch(job_ids: list, html_cache: dict) -> None:
    """Etapa de fetch (só rede): baixa o HTML das vagas ainda não cacheadas e
    salva no cache (job_html), SEM extrair skills nem gravar em jobs/job_skills.
    Idempotente pelo cache; Ctrl-C é seguro (cada HTML é salvo imediatamente)."""
    total = len(job_ids)
    baixadas = 0
    for idx, job_id in enumerate(job_ids, start=1):
        jid = str(job_id)
        if jid in html_cache:
            print(f"[{idx}/{total}] {job_id} já no cache, pulando", flush=True)
            continue

        print(f"[{idx}/{total}] baixando {job_id} …", flush=True)
        html = fetch_html(DETAIL_URL.format(job_id))
        if not html:
            print("  → resposta vazia, pulando.", flush=True)
            continue
        html_store.save_html(job_id, html)
        html_cache[jid] = html
        baixadas += 1

        delay = _random_delay()
        print(f"  → ok ({len(html)} bytes); aguardando {delay:.1f}s …", flush=True)
        time.sleep(delay)

    print(f"\nFetch concluído: {baixadas} novas vagas salvas no cache.", flush=True)


# ===========================================================================
# Main
# ===========================================================================
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extrai skills/modalidade de vagas do LinkedIn (regex)."
    )
    parser.add_argument(
        "--stage",
        choices=["fetch", "extract", "all"],
        default="all",
        help=(
            "fetch: só BAIXA o HTML das vagas (job_ids.csv) para o cache, sem extrair. "
            "extract: só EXTRAI skills/modalidade do HTML já em cache (offline) → destino. "
            "all (padrão): baixa o que faltar e já extrai, numa passada só."
        ),
    )
    args = parser.parse_args()

    html_cache = html_store.load_html_map()

    if args.stage == "extract":
        if not html_cache:
            print("Cache de HTML vazio. Rode '--stage fetch' antes.", flush=True)
            sys.exit(1)
        job_ids = list(html_cache.keys())
    else:  # fetch | all → precisam da lista-semente de IDs
        job_ids = load_job_ids()
        if not job_ids:
            print(f"Nenhum job_id em {JOB_IDS_CSV}. Rode collect_job_ids.py antes.", flush=True)
            sys.exit(1)

    print(f"=== scrape_html_rule (stage={args.stage}) ===", flush=True)

    if args.stage == "fetch":
        run_fetch(job_ids, html_cache)
        print(f"\nPronto. HTML salvo no cache "
              f"({'tabela job_html' if config.STORAGE_BACKEND == 'database' else 'data/job_html.csv'}).",
              flush=True)
        return

    run(job_ids, allow_fetch=(args.stage == "all"), html_cache=html_cache)
    destino = (
        f"tabelas jobs/job_skills em {config.DB_NAME}@{config.DB_HOST}"
        if config.STORAGE_BACKEND == "database"
        else OUTPUT_JSON.name
    )
    print(f"\nPronto. {destino} atualizado.", flush=True)


if __name__ == "__main__":
    main()