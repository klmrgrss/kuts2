# app/seed_test_data.py
import sys
import os
from pathlib import Path
import datetime

# --- Robust Path Setup ---
# This setup works whether the script is run from a directory structure
# like `/project/app/seed_test_data.py` (local) or `/app/app/seed_test_data.py` (Railway).
# It ensures the project's root is on the Python path for correct module imports.
try:
    # This will work for local execution where 'app' is a direct child of the project root.
    from database import setup_database
    from auth.utils import get_password_hash
    from auth.roles import APPLICANT
except ImportError:
    # If the first import fails, it's likely because we are in a nested 'app' directory (like on Railway).
    # We add the parent directory to the path and try again.
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    
    from app.database import setup_database
    from app.auth.utils import get_password_hash
    from app.auth.roles import APPLICANT
# --- End Path Setup ---


# --- Test Data Definitions ---

# --- Level 5 Applicants ---
APPLICANT_L5_PASS = {
    "user": {
        "email": "level5.pass@example.com",
        "full_name": "Viies Viieline",
        "birthday": "1990-05-15",
        "password": "Password123!",
        "national_id": "39005150005"
    },
    "qualification": {
        "qualification_name": "Üldehituslik ehitamine",
        "level": "Ehituse tööjuht, TASE 5",
        "specialisation": "Kivikonstruktsioonide ehitamine",
        "activity": "Üldehituslik ehitamine"
    },
    "experience": [
        {
            "role": "Objektijuht", "object_address": "Torni 7, Tallinn",
            "start_date": "2020-01", "end_date": "2021-12", # 2 years
            "contract_type": "PTV",
            "company_name": "Nordic Build AS", "company_code": "10020304",
            "client_name": "Riigi Kinnisvara AS", "permit_required": 1
        },
        {
            "role": "Tööjuht", "object_address": "Pargi 12, Tartu",
            "start_date": "2022-01", "end_date": "2022-12", # 1 year
            "contract_type": "ATV",
            "company_name": "Lõuna Ehitus OÜ", "company_code": "11223344",
            "client_name": "Tartu Ülikool", "permit_required": 0
        },
        {
            "role": "Ehitusinsener", "object_address": "Kesk 5, Pärnu",
            "start_date": "2019-01", "end_date": "2019-12", # 1 year
            "contract_type": "PTVO",
            "company_name": "Pärnu Koduagentuur", "company_code": "55667788",
            "client_name": "Eraklient", "permit_required": 1
        }
    ] # Total: 4 years
}

APPLICANT_L5_FAIL = {
    "user": {
        "email": "level5.fail@example.com",
        "full_name": "Viies Puudulik",
        "birthday": "1988-11-20",
        "password": "Password123!",
        "national_id": "48811200005"
    },
    "qualification": {
        "qualification_name": "Sisekliima tagamise süsteemide ehitamine",
        "level": "Ehituse tööjuht, TASE 5",
        "specialisation": "Küttesüsteemide ehitamine",
        "activity": "Sisekliima tagamise süsteemide ehitamine"
    },
    "experience": [
        {
            "role": "Abiline", "object_address": "Mere pst 1, Pärnu",
            "start_date": "2022-01", "end_date": "2023-06", # 1.5 years
        }
    ] # Total: 1.5 years, fails tj5_variant_1 (needs 3 total)
}

# --- Level 6 Applicants ---
APPLICANT_L6_PASS = {
    "user": {
        "email": "level6.pass@example.com",
        "full_name": "Kuues Kuldne",
        "birthday": "1985-01-01",
        "password": "Password123!",
        "national_id": "38501010006"
    },
    "qualification": {
        "qualification_name": "Üldehituslik ehitamine",
        "level": "Ehitusjuht, TASE 6",
        "specialisation": "Puitkonstruktsioonide ehitamine",
        "activity": "Üldehituslik ehitamine"
    },
    "experience": [
        {
            "role": "Projektijuht", "object_address": "Metsa 2, Viljandi",
            "start_date": "2021-01", "end_date": "2023-12", # 3 years
        }
    ] # Total: 3 years, should pass ej6_deg_matched_300 (needs 2 matching)
}

APPLICANT_L6_FAIL = {
    "user": {
        "email": "level6.fail@example.com",
        "full_name": "Kuues Koba",
        "birthday": "1987-03-03",
        "password": "Password123!",
        "national_id": "38703030006"
    },
    "qualification": {
        "qualification_name": "Ühisveevärgi või kanalisatsiooni ehitamine",
        "level": "Ehitusjuht, TASE 6",
        "specialisation": "Valikkompetentsid puuduvad",
        "activity": "Ühisveevärgi või kanalisatsiooni ehitamine"
    },
    "experience": [
        {
            "role": "Insener", "object_address": "Jõe 1, Narva",
            "start_date": "2023-01", "end_date": "2023-12", # 1 year
        }
    ] # Total: 1 year, fails ej6_deg_matched_300 (needs 2 matching)
}


TEST_APPLICANTS = [APPLICANT_L5_PASS, APPLICANT_L5_FAIL, APPLICANT_L6_PASS, APPLICANT_L6_FAIL]

def clear_previous_test_data(db):
    """Deletes records for test users to ensure a clean slate."""
    print("--- Clearing previous test data ---")
    users_table = db.t.users
    quals_table = db.t.applied_qualifications
    exp_table = db.t.work_experience
    
    for applicant in TEST_APPLICANTS:
        email = applicant["user"]["email"]
        users_table.delete_where("email = ?", [email])
        quals_table.delete_where("user_email = ?", [email])
        exp_table.delete_where("user_email = ?", [email])
        print(f"  - Cleared data for {email}")
    print("--- Cleanup complete ---")


def populate_test_data(db):
    """Hashes passwords and inserts all test data into the database."""
    print("\n--- Populating database with new test data ---")
    users_table = db.t.users
    quals_table = db.t.applied_qualifications
    exp_table = db.t.work_experience
    
    for applicant in TEST_APPLICANTS:
        user_info = applicant["user"]
        email = user_info["email"]
        
        # 1. Create User with all required fields
        hashed_password = get_password_hash(user_info["password"])
        users_table.insert({
            "email": email,
            "hashed_password": hashed_password,
            "full_name": user_info["full_name"],
            "birthday": user_info["birthday"],
            "role": APPLICANT, # Explicitly set the role
            "national_id_number": user_info.get("national_id"), # Add national ID
        }, pk='email')
        print(f"  - Created user: {email}")

        # 2. Add Applied Qualification
        qual_info = applicant["qualification"]
        quals_table.insert({
            "user_email": email,
            **qual_info # Unpack the rest of the qualification data
        })
        print(f"    - Added qualification: {qual_info['level']} - {qual_info['qualification_name']}")

        # 3. Add Work Experiences
        for exp in applicant["experience"]:
            exp_table.insert({
                "user_email": email,
                "associated_activity": qual_info["activity"],
                "start_date": exp.get("start_date"),
                "end_date": exp.get("end_date"),
                "role": exp.get("role"),
                "object_address": exp.get("object_address"),
                "contract_type": exp.get("contract_type"),
                "company_name": exp.get("company_name", "Ehitus OÜ"),
                "company_code": exp.get("company_code"),
                "client_name": exp.get("client_name"),
                "work_description": exp.get("work_description", "Töö teostatud automaatse testi raames."),
                "permit_required": exp.get("permit_required", 1),
                "ehr_code": exp.get("ehr_code", "123456789")
            })
        print(f"    - Added {len(applicant['experience'])} work experience record(s)")

    print("--- Population complete ---")


if __name__ == "__main__":
    print("Connecting to the database...")
    db_connection = setup_database()
    
    if db_connection:
        try:
            clear_previous_test_data(db_connection)
            populate_test_data(db_connection)
            print("\n✅ Successfully seeded database with 4 test applications.")
        except Exception as e:
            print(f"\n❌ An error occurred: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # fastlite manages connections, so no explicit close is needed.
            pass
    else:
        print("❌ Could not establish a database connection.")