-- migrations/004_create_evaluations_table.sql

CREATE TABLE IF NOT EXISTS evaluations (
    id INTEGER PRIMARY KEY,
    qual_id TEXT NOT NULL UNIQUE, -- The unique identifier for the application, e.g., "email-level-activity"
    evaluator_email TEXT NOT NULL,
    evaluation_state_json TEXT, -- To store the entire state object as a JSON string
    is_finalized INTEGER DEFAULT 0,
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Create an index for fast lookups by qual_id
CREATE INDEX IF NOT EXISTS ix_evaluations_qual_id ON evaluations (qual_id);