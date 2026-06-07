from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator

from datetime import datetime
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def _run_script(rel_path: str) -> None:
    script_path = BASE_DIR / rel_path
    subprocess.run([sys.executable, str(script_path)], check=True)


def scrape_jobs() -> None:
    _run_script("extracts/linkedin-get-jobs.py")


def scrape_job_details() -> None:
    _run_script("extracts/linkedin-get-jobs-detail.py")


def extract_skills() -> None:
    _run_script("extracts/extract-skills.py")


def export_dataset() -> None:
    # Placeholder: if you have a separate export script, point to it here.
    # For now this runs the skills extractor as a stub.
    _run_script("extracts/extract-skills.py")


with DAG(
    dag_id="linkedin_jobs_pipeline",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["portfolio", "linkedin"],
) as dag:

    scrape_task = PythonOperator(
        task_id="scrape_jobs",
        python_callable=scrape_jobs,
    )

    detail_task = PythonOperator(
        task_id="scrape_job_details",
        python_callable=scrape_job_details,
    )

    skills_task = PythonOperator(
        task_id="extract_skills",
        python_callable=extract_skills,
    )

    # export_task = PythonOperator(
    #     task_id="export_dataset",
    #     python_callable=export_dataset,
    # )

    #scrape_task >> detail_task >> skills_task >> export_task
    scrape_task >> detail_task >> skills_task
    #skills_task