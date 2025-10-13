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

# Applicant 1: "Perfect" candidate with 5 years of non-overlapping experience
APPLICANT_PERFECT = {
    "user": {
        "email": "perfect.candidate@example.com",
        "full_name": "Peeter Paigas",
        "birthday": "1990-05-15",
        "password": "Password123!",
        "national_id": "39005150001" # Added national_id for completeness
    },
    "qualification": {
        "qualification_name": "Üldehituslik ehitamine",
        "level": "Ehituse tööjuht, TASE 5",
        "specialisation": "Kivikonstruktsioonide ehitamine",
        "activity": "Üldehituslik ehitamine"
    },
    "experience": [
        {
            "role": "Objektijuht",
            "object_address": "Torni 7, Tallinn",
            "start_date": "2020-01", # 2 years
            "end_date": "2021-12",
        },
        {
            "role": "Tööjuht",
            "object_address": "Pargi 12, Tartu",
            "start_date": "2022-01", # 3 years
            "end_date": "2024-12",
        }
    ]
}

# Applicant 2: Candidate with overlapping work experience
APPLICANT_OVERLAPPING = {
    "user": {
        "email": "overlapping.experience@example.com",
        "full_name": "Kati Kattuv",
        "birthday": "1988-11-20",
        "password": "Password123!",
        "national_id": "48811200002" # Added national_id for completeness
    },
    "qualification": {
        "qualification_name": "Üldehituslik ehitamine",
        "level": "Ehituse tööjuht, TASE 5",
        "specialisation": "Betoonkonstruktsioonide ehitamine",
        "activity": "Üldehituslik ehitamine"
    },
    "experience": [
        {
            "role": "Projektijuhi assistent",
            "object_address": "Mere pst 1, Pärnu",
            "start_date": "2020-01", # 24 months
            "end_date": "2021-12",
        },
        {
            "role": "Apats Tööjuht",
            "object_address": "Ranna 5, Haapsalu",
            "start_date": "2021-07", # 24 months (Overlaps by 6 months)
            "end_date": "2023-06",
        }
    ]
}

TEST_APPLICANTS = [APPLICANT_PERFECT, APPLICANT_OVERLAPPING]

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
        print(f"    - Added qualification: {qual_info['qualification_name']}")

        # 3. Add Work Experiences
        for exp in applicant["experience"]:
            exp_table.insert({
                "user_email": email,
                "associated_activity": qual_info["activity"],
                "start_date": exp.get("start_date"),
                "end_date": exp.get("end_date"),
                "role": exp.get("role"),
                "object_address": exp.get("object_address"),
                "company_name": f"{user_info['full_name']} Holding",
                "work_description": "Work performed for automated testing.",
                "permit_required": 1
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
            print("\n✅ Successfully seeded database with 2 test applications.")
        except Exception as e:
            print(f"\n❌ An error occurred: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # fastlite manages connections, so no explicit close is needed.
            pass
    else:
        print("❌ Could not establish a database connection.")