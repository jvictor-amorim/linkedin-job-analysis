from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator

from datetime import datetime
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def _run_script(rel_path: str, *args: str) -> None:
    script_path = BASE_DIR / rel_path
    subprocess.run([sys.executable, str(script_path), *args], check=True)


def collect_job_ids() -> None:
    _run_script("extract/linkedin_jobs/collect_job_ids.py")


def scrape_skills() -> None:
    _run_script("extract/scrape_html_rule/scrape_html_rule.py")


def load_dataset() -> None:
    _run_script("load/load.py")


with DAG(
    dag_id="linkedin_jobs_pipeline",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["portfolio", "linkedin"],
) as dag:

    ids_task = PythonOperator(
        task_id="collect_job_ids",
        python_callable=collect_job_ids,
    )

    skills_task = PythonOperator(
        task_id="scrape_skills",
        python_callable=scrape_skills,
    )

    load_task = PythonOperator(
        task_id="load_dataset",
        python_callable=load_dataset,
    )

    ids_task >> skills_task >> load_task