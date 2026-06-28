#!/usr/bin/env python3
import csv
import os
import re
import sys
import time
import random
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# Bootstrap: sobe até achar o pacote `common` e o coloca no sys.path.
_root = Path(__file__).resolve()
while not (_root / "common").is_dir():
    _root = _root.parent
sys.path.insert(0, str(_root))

# common.config já carrega o .env (override=True) e centraliza paths/delays.
from common.config import DATA_DIR, REQUEST_DELAY_MIN, REQUEST_DELAY_MAX

OUTPUT_CSV = DATA_DIR / "job_ids.csv"
SEARCH_TERMS = [
    # --- Engenharia de Dados (Data Engineering) ---
    # "engenheiro-de-dados",
    # "engenheiro-de-dados-junior",
    # "engenheiro-de-dados-pleno",
    # "engenheiro-de-dados-senior",
    # "engenheiro-de-dados-jr",
    # "engenheiro-de-dados-pl",
    # "engenheiro-de-dados-sr",
    # "data-engineer",
    # "data-engineer-junior",
    # "data-engineer-pleno",
    # "data-engineer-senior",
    # "data-engineer-jr",
    # "data-engineer-pl",
    "data-engineer-sr",

    # --- Análise de Dados (Data Analytics) ---
    "analista-de-dados",
    "analista-de-dados-junior",
    "analista-de-dados-pleno",
    "analista-de-dados-senior",
    "analista-de-dados-jr",
    "analista-de-dados-pl",
    "analista-de-dados-sr",
    "data-analyst",
    "data-analyst-junior",
    "data-analyst-pleno",
    "data-analyst-senior",
    "data-analyst-jr",
    "data-analyst-pl",
    "data-analyst-sr",

    # --- Ciência de Dados (Data Science) ---
    "cientista-de-dados",
    "cientista-de-dados-junior",
    "cientista-de-dados-pleno",
    "cientista-de-dados-senior",
    "cientista-de-dados-jr",
    "cientista-de-dados-pl",
    "cientista-de-dados-sr",
    "data-scientist",
    "data-scientist-junior",
    "data-scientist-pleno",
    "data-scientist-senior",
    "data-scientist-jr",
    "data-scientist-pl",
    "data-scientist-sr",
]

# Usamos apenas o TEMPLATE que aceita o TERMO e o START
SEARCH_URL_TEMPLATE = (
    "https://br.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/{}-vagas?start={}"
)

# Number of pagination steps to fetch. Each step advances by 10 results.
max_pagination_steps = int(os.getenv("MAX_PAGINATION_STEPS") or 1)
print(f"Configured MAX_PAGINATION_STEPS={max_pagination_steps}")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
ID_PATTERN = re.compile(r'data-entity-urn="urn:li:jobPosting:(\d+)"')

def _random_delay_seconds() -> float:
    return random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)


def fetch_text(url: str) -> str:    
    request = Request(url, headers=HEADERS)
    try:
        with urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", errors="replace")
    except (HTTPError, URLError) as exc:
        print(f"Failed to fetch {url}: {exc}", file=sys.stderr)
        return ""


def extract_job_ids(text: str) -> list[str]:
    return [match.group(1) for match in ID_PATTERN.finditer(text)]


def load_existing_job_ids() -> set[str]:
    """Load already-saved job IDs from the CSV."""
    if OUTPUT_CSV.exists():
        try:
            with OUTPUT_CSV.open("r", encoding="utf-8", newline="") as fh:
                reader = csv.DictReader(fh)
                return {row["job_id"] for row in reader if row.get("job_id")}
        except IOError:
            return set()
    return set()


def append_job_ids(job_ids: list[str], url: str) -> None:
    """Append new job IDs to the CSV, writing the header if the file is new."""
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    write_header = not OUTPUT_CSV.exists() or OUTPUT_CSV.stat().st_size == 0
    with OUTPUT_CSV.open("a", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        if write_header:
            writer.writerow(["job_id", "url"])
        writer.writerows((job_id, url) for job_id in job_ids)
    print(f"Appended {len(job_ids)} new ids to {OUTPUT_CSV}")


def collect_job_ids() -> list[str]:
    seen = set()
    results = []
    existing_ids = load_existing_job_ids()
    print(f"Loaded {len(existing_ids)} previously saved job IDs from {OUTPUT_CSV}")

    for term in SEARCH_TERMS:
        print(f"\n--- Collecting job IDs for term: {term} ---")
        page = 0
        while page < max_pagination_steps:
            start = page * 10
            url = SEARCH_URL_TEMPLATE.format(term, start)
            print(f"Fetching page {page + 1}/{max_pagination_steps} for '{term}': {url}")
            page_text = fetch_text(url)
            ids = extract_job_ids(page_text)
            if not ids:
                print(f"No job IDs found on this page for '{term}'. Stopping this term.")
                break

            # Filter out already-saved IDs (avoid redundant processing) and current-session duplicates
            new_ids = [job_id for job_id in ids if job_id not in seen and job_id not in existing_ids]
            if not new_ids:
                print("No new IDs on this page (all duplicates), continuing to next page.")
            else:
                # Persist this page's IDs immediately so progress survives interruptions
                append_job_ids(new_ids, url)

            for job_id in new_ids:
                seen.add(job_id)
                results.append(job_id)

            page += 1

            if page >= max_pagination_steps:
                print(f"Reached configured pagination limit of {max_pagination_steps} pages for '{term}'.")

            # Sleep a random amount between pages to avoid rate limiting
            sleep_s = _random_delay_seconds()
            print(f"Sleeping {sleep_s:.1f} seconds before next page request")
            time.sleep(sleep_s)

    return results


def main() -> None:
    job_ids = collect_job_ids()
    if not job_ids:
        print("No job IDs were collected.")
        return
    print(f"Collected {len(job_ids)} new job ids in total.")


if __name__ == "__main__":
    main()