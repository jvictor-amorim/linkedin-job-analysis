import csv
import json
from openai import OpenAI
import os
from dotenv import load_dotenv
from pathlib import Path
import time

# Load environment variables from the project .env (mounted at /opt/airflow/.env in the container).
# override=True so runtime edits to .env win over stale values baked in at container creation.
load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)
# support both LLM_API_KEY and OPENAI_API_KEY environment variables
api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")

if not api_key:
    raise RuntimeError("OPENAI_API_KEY or LLM_API_KEY not set in environment or .env")

class ConnectLLM(OpenAI):
    def __init__(self, api_key: str):
        super().__init__(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1"
        )
client = ConnectLLM(api_key=api_key)

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
JOBS_CSV = BASE_DIR / "files" / "jobs.csv"
TECHNICAL_SKILLS_CSV = BASE_DIR / "normalize" / "technical-skills.csv"
SOFT_SKILLS_CSV = BASE_DIR / "normalize" / "soft-skills.csv"
# Keep output.json inside extracts/files so it lands in the volume mounted by docker-compose
OUTPUT_JSON = BASE_DIR / "files" / "output.json"


def load_output_json(path: Path):
    if path.exists():
        content = path.read_text(encoding="utf-8").strip()
        if content:
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return []
    return []


def save_output_json(path: Path, data):
    with path.open(mode="w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def parse_llm_json(text: str):
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass
    return {"raw_output": text}


technical_skills = []
if not TECHNICAL_SKILLS_CSV.exists():
    raise FileNotFoundError(f"technical-skills.csv not found at {TECHNICAL_SKILLS_CSV}. Please ensure it exists.")
with TECHNICAL_SKILLS_CSV.open(mode='r', encoding='utf-8') as file:
    technical_skills = list(csv.reader(file))
    technical_skills = technical_skills[1:]  # Skip header row

soft_skills = []
if not SOFT_SKILLS_CSV.exists():
    raise FileNotFoundError(f"soft-skills.csv not found at {SOFT_SKILLS_CSV}. Please ensure it exists.")
with SOFT_SKILLS_CSV.open(mode='r', encoding='utf-8') as file:
    soft_skills = list(csv.reader(file))
    soft_skills = soft_skills[1:]  # Skip header row

output_data = load_output_json(OUTPUT_JSON)
processed_job_ids = {str(item.get("job_id")) for item in output_data if item.get("job_id") is not None}

if not JOBS_CSV.exists():
    raise FileNotFoundError(f"jobs.csv not found at {JOBS_CSV}. Run linkedin-get-jobs-detail.py first to generate it.")
with JOBS_CSV.open(mode='r', encoding='utf-8') as file:
    data = list(csv.reader(file))
    data = data[1:]  # Skip header row
    for row in data:
        job_id, detail = row
        if str(job_id) in processed_job_ids:
            print(f"Skipping job {job_id}: already processed in {OUTPUT_JSON}")
            continue

        print(f"Job ID: {job_id}")
        print(f"Detail: {detail[:200]}...")  # Print first 200 characters of detail
        print("-" * 40)
        time.sleep(61)  # Sleep before each LLM call to avoid rate limits
        prompt = f"Extract the skills required for the following job description:\n\n{detail}."
        prompt += "\n\nReturn the skills in format JSON"
        prompt += "\n\nNormaize skills to the following technical skills list: " + ", ".join([skill[0] for skill in technical_skills])
        prompt += "\n\nNormaize skills to the following soft skills list: " + ", ".join([skill[0] for skill in soft_skills])
        prompt += "\n\nAdding classification of experience level (entry, mid, senior) is a plus but optional."
        prompt += "\n\nOnly return skills that are in the provided lists. If no skills are found, return an empty list."
        prompt += """Example output:
        {   
            "level": "mid",
            "technical_skills": ["Python", "Django"],
            "soft_skills": ["Communication", "Teamwork"]
        }"""
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        skills = response.choices[0].message.content.strip()
        print(f"Extracted Skills: {skills}")

        skills_obj = parse_llm_json(skills)
        output_entry = {
            "job_id": job_id,
            "skills": skills_obj
        }
        output_data.append(output_entry)
        save_output_json(OUTPUT_JSON, output_data)
        processed_job_ids.add(str(job_id))