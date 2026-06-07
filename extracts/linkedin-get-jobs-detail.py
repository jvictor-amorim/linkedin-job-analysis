#!/usr/bin/env python3
import csv
import re
import sys
import os
import time
import random
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE_DIR = Path(__file__).resolve().parent
JOB_IDS_CSV = BASE_DIR / "files" / "linkedin-job-ids.csv"
OUTPUT_CSV = BASE_DIR / "files" / "jobs.csv"
DETAIL_URL = "https://br.linkedin.com/jobs-guest/jobs/api/jobPosting/{}?trackingId=A0o19CoqjHvSsa6GcDT4yg%3D%3D"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

WHITESPACE_PATTERN = re.compile(r"\s+")

# Request delay configuration (seconds). Set via environment variables for easy changes.
REQUEST_DELAY_MIN = int(os.getenv("REQUEST_DELAY_MIN", "5"))
REQUEST_DELAY_MAX = int(os.getenv("REQUEST_DELAY_MAX", "15"))

def _random_delay_seconds() -> float:
    return random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)


class SelectorTextExtractor(HTMLParser):
    def __init__(self, target_class: str):
        super().__init__()
        self.target_class = target_class
        self._texts = []
        self._capture_depth = 0
        self._skip = False

    def _is_target_element(self, attrs: list[tuple[str, str]]) -> bool:
        for name, value in attrs:
            if name == "class" and value:
                class_names = value.split()
                if self.target_class in class_names:
                    return True
        return False

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self._skip = True
        if self._capture_depth > 0:
            self._capture_depth += 1
        elif self._is_target_element(attrs):
            self._capture_depth = 1

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self._skip = False
        if self._capture_depth > 0:
            self._capture_depth -= 1

    def handle_data(self, data):
        if self._capture_depth > 0 and not self._skip:
            self._texts.append(data)

    def get_text(self):
        return " ".join(self._texts).strip()


def fetch_text(url: str) -> str:
    request = Request(url, headers=HEADERS)
    try:
        with urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", errors="replace")
    except (HTTPError, URLError) as exc:
        print(f"Failed to fetch {url}: {exc}", file=sys.stderr)
        return ""


def load_job_ids() -> list[str]:
    if not JOB_IDS_CSV.exists():
        return []
    with JOB_IDS_CSV.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        return [row.get("job_id") for row in reader if row.get("job_id")]


def extract_body_text(html: str) -> str:
    parser = SelectorTextExtractor("decorated-job-posting__details")
    parser.feed(html)
    raw_text = parser.get_text()
    cleaned_text = WHITESPACE_PATTERN.sub(" ", raw_text).strip()
    return cleaned_text


def fetch_job_detail(job_id: str) -> str:
    url = DETAIL_URL.format(job_id)
    print(f"Fetching detail for job ID {job_id}")
    html = fetch_text(url)
    return extract_body_text(html)


def save_jobs_csv(rows: list[tuple[str, str]]) -> None:
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["job_id", "detail"])
        writer.writerows(rows)
    print(f"Saved {len(rows)} job details to {OUTPUT_CSV}")


def main() -> None:
    job_ids = load_job_ids()
    if not job_ids:
        print(f"No job IDs found in {JOB_IDS_CSV}. Run extracts/linkedin-get-jobs.py first.")
        return

    # Load existing CSV rows (if any) so we can skip already-processed jobs
    existing = {}
    if OUTPUT_CSV.exists():
        with OUTPUT_CSV.open("r", encoding="utf-8", newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                job_id = row.get("job_id") or row.get("id")
                if job_id:
                    existing[job_id] = row.get("detail", "")

    # Process job IDs: skip if a non-empty detail already exists in jobs.csv
    for job_id in job_ids:
        current_detail = existing.get(job_id)
        if current_detail is not None and str(current_detail).strip() != "":
            print(f"Skipping job {job_id}: detail already present in {OUTPUT_CSV}")
            continue

        detail_text = fetch_job_detail(job_id)
        existing[job_id] = detail_text

        # Sleep a random amount between requests to avoid rate limits
        sleep_s = _random_delay_seconds()
        print(f"Sleeping {sleep_s:.1f} seconds before next job request")
        time.sleep(sleep_s)

    # Save merged results back to CSV preserving any previously stored entries
    rows = [(job_id, existing[job_id]) for job_id in existing]
    save_jobs_csv(rows)


if __name__ == "__main__":
    main()


