#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent


def run(rel_path: str, *args: str) -> None:
    script_path = BASE / rel_path
    print(f"Running {script_path} {' '.join(args)}".rstrip())
    res = subprocess.run([sys.executable, str(script_path), *args])
    if res.returncode != 0:
        print(f"Script {rel_path} failed with exit code {res.returncode}")
        raise SystemExit(res.returncode)


if __name__ == "__main__":
    # extract (coleta de ids + scrape/regex de skills) -> load
    run("extract/linkedin_jobs/collect_job_ids.py")
    run("extract/scrape_html_rule/scrape_html_rule.py")
    run("load/load.py")
    print("Pipeline finished successfully")
