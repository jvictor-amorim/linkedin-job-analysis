#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent

def run(script_name: str) -> None:
    script_path = BASE / "extracts" / script_name
    print(f"Running {script_path}")
    res = subprocess.run([sys.executable, str(script_path)])
    if res.returncode != 0:
        print(f"Script {script_name} failed with exit code {res.returncode}")
        raise SystemExit(res.returncode)


if __name__ == "__main__":
    # sequence: collect ids -> fetch details -> extract skills
    run("linkedin-get-jobs.py")
    run("linkedin-get-jobs-detail.py")
    run("skills.py")
    print("Pipeline finished successfully")
