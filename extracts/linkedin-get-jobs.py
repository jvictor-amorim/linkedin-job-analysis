#!/usr/bin/env python3
import csv
import os
import re
import sys
import time
import random
from pathlib import Path
from dotenv import load_dotenv
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_CSV = BASE_DIR / "files" / "linkedin-job-ids.csv"
SEARCH_URL = "https://br.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/engenheiro-de-dados-vagas?start={}"
# Load environment variables from the project .env (mounted at /opt/airflow/.env in the container).
# override=True so runtime edits to .env win over stale values baked in at container creation.
load_dotenv(BASE_DIR.parent / ".env", override=True)

# Number of pagination steps to fetch. Each step advances by 10 results.
max_pagination_steps = int(os.getenv("MAX_PAGINATION_STEPS") or 1)
print(f"Configured MAX_PAGINATION_STEPS={max_pagination_steps}")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
ID_PATTERN = re.compile(r'data-entity-urn="urn:li:jobPosting:(\d+)"')

# Request delay configuration (seconds). Set via environment variables for easy changes.
REQUEST_DELAY_MIN = int(os.getenv("REQUEST_DELAY_MIN", "5"))
REQUEST_DELAY_MAX = int(os.getenv("REQUEST_DELAY_MAX", "15"))

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


def collect_job_ids() -> list[str]:
    page = 0
    seen = set()
    results = []
    existing_ids = load_existing_job_ids()
    print(f"Loaded {len(existing_ids)} previously saved job IDs from {OUTPUT_CSV}")

    while page < max_pagination_steps:
        start = page * 10
        url = SEARCH_URL.format(start)
        print(f"Fetching page {page + 1}/{max_pagination_steps}: {url}")
        page_text = fetch_text(url)
        ids = extract_job_ids(page_text)
        if not ids:
            print("No job IDs found on this page. Stopping.")
            break

        # Filter out already-saved IDs (avoid redundant processing) and current-session duplicates
        new_ids = [job_id for job_id in ids if job_id not in seen and job_id not in existing_ids]
        if not new_ids:
            print("No new IDs on this page (all duplicates), continuing to next page.")

        for job_id in new_ids:
            seen.add(job_id)
            results.append(job_id)

        page += 1

        if page >= max_pagination_steps:
            print(f"Reached configured pagination limit of {max_pagination_steps} pages.")

        # Sleep a random amount between pages to avoid rate limiting
        sleep_s = _random_delay_seconds()
        print(f"Sleeping {sleep_s:.1f} seconds before next page request")
        time.sleep(sleep_s)
    return results, url


def save_job_ids(job_ids: list[str], url: str) -> None:
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    existing_rows = []
    existing_ids = set()
    if OUTPUT_CSV.exists():
        with OUTPUT_CSV.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                job_id = row.get("job_id")
                if job_id:
                    existing_rows.append((job_id, row.get("url", "")))
                    existing_ids.add(job_id)

    new_rows = list(existing_rows)
    for job_id in job_ids:
        if job_id not in existing_ids:
            new_rows.append((job_id, url))
            existing_ids.add(job_id)

    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["job_id", "url"])
        writer.writerows(new_rows)

    print(f"Saved {len(new_rows)} ids to {OUTPUT_CSV} ({len(job_ids)} new ids appended)")


def main() -> None:
    job_ids, url = collect_job_ids()
    if not job_ids:
        print("No job IDs were collected.")
        return
    save_job_ids(job_ids, url)


if __name__ == "__main__":
    main()