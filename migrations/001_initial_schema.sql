PRAGMA foreign_keys=OFF;

CREATE TABLE IF NOT EXISTS users (
    email TEXT PRIMARY KEY,
    hashed_password TEXT,
    full_name TEXT,
    birthday TEXT,
    role TEXT NOT NULL DEFAULT 'applicant' CHECK(role IN ('applicant','evaluator','admin')),
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS applicant_profile (
    user_email TEXT PRIMARY KEY,
    full_name TEXT,
    address TEXT,
    phone TEXT,
    FOREIGN KEY(user_email) REFERENCES users(email) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS existing_qualifications (
    id INTEGER PRIMARY KEY,
    user_email TEXT,
    qualification_name TEXT,
    level TEXT,
    specialisation TEXT,
    activity TEXT,
    issue_date TEXT,
    expiry_date TEXT,
    certificate_number TEXT
);
CREATE INDEX IF NOT EXISTS ix_existing_qualifications_user_email ON existing_qualifications(user_email);

CREATE TABLE IF NOT EXISTS applied_qualifications (
    id INTEGER PRIMARY KEY,
    user_email TEXT,
    qualification_name TEXT,
    level TEXT,
    specialisation TEXT,
    activity TEXT,
    is_renewal INTEGER,
    application_date TEXT,
    eval_education_status TEXT,
    eval_training_status TEXT,
    eval_experience_status TEXT,
    eval_comment TEXT,
    eval_decision TEXT
);
CREATE INDEX IF NOT EXISTS ix_applied_qualifications_user_email ON applied_qualifications(user_email);

CREATE TABLE IF NOT EXISTS work_experience (
    id INTEGER PRIMARY KEY,
    user_email TEXT,
    application_id TEXT,
    competency TEXT,
    other_work TEXT,
    object_address TEXT,
    object_purpose TEXT,
    ehr_code TEXT,
    construction_activity TEXT,
    other_activity TEXT,
    permit_required INTEGER,
    start_date TEXT,
    end_date TEXT,
    work_description TEXT,
    role TEXT,
    other_role TEXT,
    contract_type TEXT,
    company_name TEXT,
    company_code TEXT,
    company_contact TEXT,
    company_email TEXT,
    company_phone TEXT,
    client_name TEXT,
    client_code TEXT,
    client_contact TEXT,
    client_email TEXT,
    client_phone TEXT,
    work_keywords TEXT,
    associated_activity TEXT
);
CREATE INDEX IF NOT EXISTS ix_work_experience_user_email ON work_experience(user_email);

CREATE TABLE IF NOT EXISTS education (
    id INTEGER PRIMARY KEY,
    user_email TEXT,
    education_level TEXT,
    institution_name TEXT,
    degree_name TEXT,
    field_of_study TEXT,
    start_year TEXT,
    end_year TEXT,
    file_path TEXT
);
CREATE INDEX IF NOT EXISTS ix_education_user_email ON education(user_email);

CREATE TABLE IF NOT EXISTS training_files (
    id INTEGER PRIMARY KEY,
    user_email TEXT,
    training_name TEXT,
    provider TEXT,
    completion_date TEXT,
    file_path TEXT
);
CREATE INDEX IF NOT EXISTS ix_training_files_user_email ON training_files(user_email);

CREATE TABLE IF NOT EXISTS employment_proof (
    id INTEGER PRIMARY KEY,
    user_email TEXT,
    proof_type TEXT,
    description TEXT,
    file_path TEXT
);
CREATE INDEX IF NOT EXISTS ix_employment_proof_user_email ON employment_proof(user_email);

PRAGMA foreign_keys=ON;
