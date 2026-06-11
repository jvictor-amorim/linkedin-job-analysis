#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scrape_html_rule.py

Abordagem por dicionário de regex (sem classificação por seção).

Passada única e idempotente: para cada job_id do data/job_ids.csv que ainda não
está no data/scrape_html_rule.json, baixa o HTML da vaga, aplica o motor de regex
de skills + detecção de modalidade sobre o texto, e grava imediatamente em
data/scrape_html_rule.json:
    { job_id, title, company, city, work_mode, skills: [...] }

A idempotência vem do próprio scrape_html_rule.json (vaga já presente é pulada,
sem rebaixar). O dicionário de skills fica em skills_dict.py (fácil de editar/agrupar).
"""

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


def _alias_pattern(alias: str) -> re.Pattern | None:
    """Compila um alias em regex que tolera junto/separado/hífen.
    Ex.: 'data integration' -> casa 'data integration', 'dataintegration',
    'data-integration'. Usa lookarounds (não \\b) para funcionar com tokens
    que têm dígitos/símbolos como 's3', 'ci/cd', 'k8s'."""
    a = _norm(alias).strip()
    tokens = [re.escape(t) for t in re.split(r"[\s/\-]+", a) if t]
    if not tokens:
        return None
    body = r"[\s\-/]*".join(tokens)
    return re.compile(rf"(?<![a-z0-9]){body}(?![a-z0-9])", re.I)


# pré-compila uma vez (canônico -> lista de padrões)
_COMPILED = {
    canon: [p for p in (_alias_pattern(a) for a in aliases) if p]
    for canon, aliases in SKILLS.items()
}


def extract_skills(text: str) -> list[str]:
    """Retorna a lista de skills canônicas encontradas no texto, ordenada.
    Cada grupo entra no máximo uma vez (agrupamento por nome canônico)."""
    if not text:
        return []
    norm = _norm(text)
    found = []
    for canon, patterns in _COMPILED.items():
        for p in patterns:
            if p.search(norm):
                found.append(canon)
                break  # achou um alias do grupo; não precisa testar os demais
    return sorted(set(found))


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
# Passada única — baixa + extrai + grava (idempotente via scrape_html_rule.json)
# ===========================================================================
def run(job_ids: list) -> None:
    """Para cada vaga ainda não presente no scrape_html_rule.json: baixa o HTML,
    extrai skills/modalidade e grava no JSON imediatamente. Vaga já no JSON é
    pulada sem rebaixar. Ctrl-C é seguro: o output é salvo a cada entrada."""
    output = load_output()
    processed = {str(item["job_id"]) for item in output if item.get("job_id")}
    total = len(job_ids)

    for idx, job_id in enumerate(job_ids, start=1):
        if str(job_id) in processed:
            print(f"[{idx}/{total}] {job_id} já no JSON, pulando", flush=True)
            continue

        print(f"[{idx}/{total}] baixando {job_id} …", flush=True)
        html = fetch_html(DETAIL_URL.format(job_id))
        if not html:
            print("  → resposta vazia, pulando.", flush=True)
            continue

        entry = build_entry(job_id, html)
        output.append(entry)
        processed.add(str(job_id))
        save_output(output)
        cargo_str = entry["title"] or "(sem cargo)"
        empresa_str = entry["company"] or "(sem empresa)"
        cidade_str = entry["city"] or "(sem cidade)"
        skills = entry["skills"]
        print(
            f"  → {cargo_str} @ {empresa_str} ({cidade_str}) "
            f"→ {len(skills)} skills: {skills[:5]} [output: {len(output)}]",
            flush=True,
        )

        delay = _random_delay()
        print(f"  → aguardando {delay:.1f}s …", flush=True)
        time.sleep(delay)


# ===========================================================================
# Main
# ===========================================================================
def main() -> None:
    job_ids = load_job_ids()
    if not job_ids:
        print(f"Nenhum job_id em {JOB_IDS_CSV}. Rode collect_job_ids.py antes.", flush=True)
        sys.exit(1)

    print("=== scrape + regex de skills ===", flush=True)
    run(job_ids)
    print(f"\nPronto. {OUTPUT_JSON.name} atualizado.", flush=True)


if __name__ == "__main__":
    main()