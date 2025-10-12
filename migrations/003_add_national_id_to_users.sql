-- Add a column to store the user's unique national identity number.
ALTER TABLE users ADD COLUMN national_id_number TEXT;

-- Create a unique index on the new column to ensure data integrity and fast lookups.
CREATE UNIQUE INDEX IF NOT EXISTS ix_users_national_id_number ON users (national_id_number);