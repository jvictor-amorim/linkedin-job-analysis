-- Schema do pipeline LinkedIn Job Analysis.
-- Modelo normalizado: uma vaga em `jobs`, uma linha por skill em `job_skills`.
-- Idempotente: pode ser executado repetidamente.

CREATE TABLE IF NOT EXISTS jobs (
    job_id     TEXT PRIMARY KEY,
    title      TEXT,
    company    TEXT,
    city       TEXT,
    work_mode  TEXT CHECK (work_mode IN ('presencial', 'remoto', 'hibrido') OR work_mode IS NULL),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS job_skills (
    job_id TEXT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    skill  TEXT NOT NULL,
    PRIMARY KEY (job_id, skill)
);

CREATE INDEX IF NOT EXISTS idx_job_skills_skill ON job_skills (skill);
CREATE INDEX IF NOT EXISTS idx_jobs_work_mode ON jobs (work_mode);
