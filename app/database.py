# database.py

from fastlite import database
import os
import traceback # Added for potentially more robust error handling if needed later

# --- Path Definition ---
script_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(script_dir, '..'))
DATA_DIR = os.path.join(project_root, 'data')
DB_FILE = os.path.join(DATA_DIR, 'applicant_data.db')
# ---

def setup_database():
    """
    Sets up the SQLite database connection and ensures tables are created.
    Includes data migration logic for work_experience date fields.
    Uses fastlite library. Uses raw SQL for index creation as workaround.
    """
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        print(f"--- Ensured data directory exists: {DATA_DIR} ---")
    except OSError as e:
        print(f"--- ERROR: Could not create data directory '{DATA_DIR}': {e} ---")
        # RAISE AN EXCEPTION INSTEAD OF RETURNING NONE
        raise RuntimeError(f"Failed to create data directory: {DATA_DIR}") from e # Added this line

    print(f"--- Setting up database at: {DB_FILE} ---")
    print(f"--- Absolute DB Path Attempting: {os.path.abspath(DB_FILE)} ---")

    try:
        db = database(DB_FILE)
    except Exception as e:
        print(f"--- FATAL ERROR: Could not open database file '{DB_FILE}': {e} ---")
        traceback.print_exc()
        # RAISE AN EXCEPTION INSTEAD OF RETURNING NONE
        raise RuntimeError(f"Failed to open database: {DB_FILE}") from e # Added this line



    # Define tables
    users = db.t.users
    applicant_profile = db.t.applicant_profile
    existing_qualifications = db.t.existing_qualifications
    applied_qualifications = db.t.applied_qualifications
    work_experience = db.t.work_experience
    education = db.t.education
    training_files = db.t.training_files
    employment_proof = db.t.employment_proof

    # === Create Users Table ===
    if users not in db.t:
        print("--- Creating 'users' table ---")
        # Schema uses TEXT for birthday (YYYY-MM-DD from flatpickr)
        users.create(email=str, hashed_password=str, full_name=str, birthday=str, pk='email')
        print("--- 'users' table created ---")

    # === Create Applicant Profile Table ===
    if applicant_profile not in db.t:
        print("--- Creating 'applicant_profile' table ---")
        applicant_profile.create(
            user_email=str, full_name=str, address=str, phone=str,
            pk='user_email'
        )
        print("--- 'applicant_profile' table created ---")

    # === Create Existing Qualifications Table ===
    if existing_qualifications not in db.t:
        print("--- Creating 'existing_qualifications' table ---")
        existing_qualifications.create(
            id=int, user_email=str, qualification_name=str, level=str,
            specialisation=str, activity=str, issue_date=str, expiry_date=str,
            certificate_number=str, pk='id'
        )
        db.execute("CREATE INDEX IF NOT EXISTS ix_existing_qualifications_user_email ON existing_qualifications (user_email)")
        print("--- 'existing_qualifications' table created ---")

    # === Create Applied Qualifications Table ===
    if applied_qualifications not in db.t:
        print("--- Creating 'applied_qualifications' table ---")
        applied_qualifications.create(
            id=int, user_email=str, qualification_name=str, level=str,
            specialisation=str, activity=str, is_renewal=int, application_date=str,
            eval_education_status=str, eval_training_status=str, eval_experience_status=str,
            eval_comment=str, eval_decision=str,
            pk='id'
        )
        db.execute("CREATE INDEX IF NOT EXISTS ix_applied_qualifications_user_email ON applied_qualifications (user_email)")
        print("--- 'applied_qualifications' table created ---")
    else:
        # Add evaluator columns if they don't exist
        print("--- Checking/Adding columns to existing 'applied_qualifications' table ---")
        existing_cols = [col[1] for col in db.execute(f"PRAGMA table_info(applied_qualifications)").fetchall()]
        new_cols = {
            "eval_education_status": "TEXT", "eval_training_status": "TEXT",
            "eval_experience_status": "TEXT", "eval_comment": "TEXT", "eval_decision": "TEXT"
        }
        for col_name, col_type in new_cols.items():
            if col_name not in existing_cols:
                try: print(f"    Adding column: {col_name}"); db.execute(f"ALTER TABLE applied_qualifications ADD COLUMN {col_name} {col_type}")
                except Exception as e: print(f"    Error adding column {col_name}: {e}")

    # === Create/Migrate Work Experience Table ===
    if work_experience not in db.t:
        print("--- Creating 'work_experience' table (New Schema) ---")
        # Create with the NEW schema directly
        work_experience.create(
            id=int, user_email=str, application_id=str, competency=str, other_work=str,
            object_address=str, object_purpose=str, ehr_code=str, construction_activity=str,
            other_activity=str, permit_required=int,
            # NEW date columns
            start_date=str, # Format: YYYY-MM
            end_date=str,   # Format: YYYY-MM
            # END NEW date columns
            work_description=str, role=str, other_role=str,
            contract_type=str, company_name=str, company_code=str, company_contact=str,
            company_email=str, company_phone=str, client_name=str, client_code=str,
            client_contact=str, client_email=str, client_phone=str, work_keywords=str,
            associated_activity=str,
            pk='id'
        )
        db.execute("CREATE INDEX IF NOT EXISTS ix_work_experience_user_email ON work_experience (user_email)")
        print("--- 'work_experience' table created ---")
    else:
        # Table exists, perform migration steps if needed
        print("--- [Work Experience] Table exists, checking schema/migrating data ---")

        # Step 1: Add New Columns if they don't exist
        print("--- [Work Experience] Checking/Adding new date columns ---")
        existing_cols_exp = [col[1] for col in db.execute(f"PRAGMA table_info(work_experience)").fetchall()]
        start_date_exists = 'start_date' in existing_cols_exp
        end_date_exists = 'end_date' in existing_cols_exp

        if not start_date_exists:
            try:
                print("    Adding column: start_date (TEXT)")
                db.execute("ALTER TABLE work_experience ADD COLUMN start_date TEXT")
                start_date_exists = True # Mark as added for subsequent steps
            except Exception as e:
                print(f"    Error adding column start_date: {e}")

        if not end_date_exists:
            try:
                print("    Adding column: end_date (TEXT)")
                db.execute("ALTER TABLE work_experience ADD COLUMN end_date TEXT")
                end_date_exists = True # Mark as added
            except Exception as e:
                print(f"    Error adding column end_date: {e}")

        # Step 2: Migrate Data (Only if new columns were added or potentially exist from previous run)
        # Check if old columns still exist before attempting migration
        old_cols_exist = all(c in existing_cols_exp for c in ['start_month', 'start_year', 'end_month', 'end_year'])

        if old_cols_exist and start_date_exists and end_date_exists: # Check if migration is possible/needed
            print("--- [Work Experience] Migrating data from old month/year columns ---")
            try:
                # Select rows that haven't been migrated (start_date is NULL) AND have old data
                rows_to_migrate = db.execute(
                    "SELECT id, start_month, start_year, end_month, end_year FROM work_experience WHERE start_date IS NULL AND (start_year IS NOT NULL AND start_month IS NOT NULL)"
                ).fetchall()
                print(f"    Found {len(rows_to_migrate)} rows potentially needing date migration.")

                updated_count = 0
                for row_dict in rows_to_migrate:
                    row_id = row_dict['id']
                    start_year = row_dict['start_year']
                    start_month = row_dict['start_month']
                    end_year = row_dict['end_year']
                    end_month = row_dict['end_month']

                    start_date_str = None
                    end_date_str = None

                    if start_year and start_month:
                        try: start_date_str = f"{start_year}-{int(start_month):02d}"
                        except (ValueError, TypeError): print(f"    WARN: Invalid start month/year ('{start_month}'/'{start_year}') for row ID {row_id}. Skipping start date.")
                    if end_year and end_month:
                        try: end_date_str = f"{end_year}-{int(end_month):02d}"
                        except (ValueError, TypeError): print(f"    WARN: Invalid end month/year ('{end_month}'/'{end_year}') for row ID {row_id}. Skipping end date.")

                    if start_date_str or end_date_str:
                        updates = []
                        params = []
                        if start_date_str:
                            updates.append("start_date = ?")
                            params.append(start_date_str)
                        if end_date_str:
                            updates.append("end_date = ?")
                            params.append(end_date_str)

                        if updates:
                            params.append(row_id)
                            update_sql = f"UPDATE work_experience SET {', '.join(updates)} WHERE id = ?"
                            db.execute(update_sql, params)
                            updated_count += 1

                print(f"--- [Work Experience] Successfully migrated dates for {updated_count} rows. ---")

            except Exception as e:
                print(f"--- ERROR during work_experience date migration: {e} ---")
                traceback.print_exc()
        elif not old_cols_exist:
             print("--- [Work Experience] Old month/year columns not found, skipping migration phase. ---")
        else:
            print("--- [Work Experience] New date columns not ready, skipping migration phase. ---")


        # Step 3: Attempt to Drop Old Columns (if they still exist)
        print("--- [Work Experience] Attempting to drop old date columns (may fail on older SQLite) ---")
        old_columns_to_drop = ['start_month', 'start_year', 'end_month', 'end_year']
        # Fetch current columns again after potential additions/migrations
        existing_cols_exp_final = [col[1] for col in db.execute(f"PRAGMA table_info(work_experience)").fetchall()]

        for col_name in old_columns_to_drop:
            if col_name in existing_cols_exp_final:
                try:
                    print(f"    Attempting to drop column: {col_name}")
                    db.execute(f"ALTER TABLE work_experience DROP COLUMN {col_name}")
                    print(f"    Successfully dropped column: {col_name}")
                except Exception as e:
                    print(f"    WARN: Could not drop column {col_name} (likely unsupported by SQLite version): {e}")
            else:
                # This case might be hit if drop was successful on a previous run
                print(f"    Column {col_name} does not exist, skipping drop.")

    # === Create Education Table ===
    if education not in db.t:
        print("--- Creating 'education' table ---")
        education.create(
            id=int, user_email=str, education_category=str, education_detail=str,
            institution=str, specialty=str,
            graduation_date=str, # Storing YYYY-MM from flatpickr
            document_storage_identifier=str,
            original_filename=str,
            pk='id'
        )
        db.execute("CREATE INDEX IF NOT EXISTS ix_education_user_email ON education (user_email)")
        print("--- 'education' table created ---")
    else:
        # Add document columns if they don't exist
        print("--- Checking/Adding columns to existing 'education' table ---")
        existing_cols_edu = [col[1] for col in db.execute(f"PRAGMA table_info(education)").fetchall()]
        new_edu_cols = {
            "document_storage_identifier": "TEXT",
            "original_filename": "TEXT"
        }
        for col_name, col_type in new_edu_cols.items():
            if col_name not in existing_cols_edu:
                try:
                    print(f"    Adding column: {col_name}")
                    db.execute(f"ALTER TABLE education ADD COLUMN {col_name} {col_type}")
                except Exception as e:
                    print(f"    Error adding column {col_name}: {e}")

    # === Create Training Files Table ===
    if training_files not in db.t:
        print("--- Creating 'training_files' table ---")
        training_files.create(
            id=int, user_email=str, applied_qualification_id=int, file_description=str,
            original_filename=str, storage_identifier=str, upload_timestamp=str, pk='id'
        )
        db.execute("CREATE INDEX IF NOT EXISTS ix_training_files_user_email ON training_files (user_email)")
        db.execute("CREATE INDEX IF NOT EXISTS ix_training_files_applied_qualification_id ON training_files (applied_qualification_id)")
        print("--- 'training_files' table created ---")

    # === Create Employment Proof Table ===
    if employment_proof not in db.t:
        print("--- Creating 'employment_proof' table ---")
        employment_proof.create(
            user_email=str, file_description=str, original_filename=str,
            storage_identifier=str, upload_timestamp=str, pk='user_email'
        )
        print("--- 'employment_proof' table created ---")

    print(f"--- Database setup complete. Tables checked/created/updated. ---")
    return db