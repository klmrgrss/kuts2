# app/promote_user.py
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
import time

# --- Setup Project Path ---
APP_PATH = Path(__file__).parent
if str(APP_PATH) not in sys.path:
    sys.path.insert(0, str(APP_PATH))
# --- End Setup ---

# Load environment variables from .env file
load_dotenv()

from database import setup_database
from auth.utils import get_password_hash # Import the password hashing utility
from fastlite import NotFoundError

def sync_evaluator_roles():
    """
    Reads evaluator emails from the environment variable 'EVALUATOR_EMAILS'.
    For each email, it ensures the user exists (creating them if necessary)
    and that their role is set to 'evaluator'.
    """
    # Wait for 5 seconds to give the volume time to mount. This is a pragmatic
    # fix for the race condition on Railway.
    print("--- Starting role sync. Waiting 5 seconds for volume to mount... ---")
    time.sleep(5)

    evaluator_emails_str = os.getenv("EVALUATOR_EMAILS")
    if not evaluator_emails_str:
        print("INFO: No EVALUATOR_EMAILS environment variable set. Nothing to sync.")
        return

    evaluator_emails = [email.strip() for email in evaluator_emails_str.split(',') if email.strip()]
    if not evaluator_emails:
        print("INFO: EVALUATOR_EMAILS variable is empty. Nothing to sync.")
        return

    print(f"--- Syncing roles for {len(evaluator_emails)} designated evaluators... ---")
    
    print("Connecting to the database...")
    db = setup_database()
    users_table = db.t.users
    
    # Use a secure, default password for any newly created evaluators.
    # The user should be instructed to change this after their first login.
    default_password = os.getenv("DEFAULT_EVALUATOR_PASSWORD", "Password123!")
    hashed_password = get_password_hash(default_password)

    for email in evaluator_emails:
        try:
            user = users_table[email]
            # User exists, check if they need promotion
            if user['role'] != 'evaluator':
                users_table.update({"role": "evaluator"}, pk=email)
                print(f"  - ✅ PROMOTED: User '{email}' role updated to 'evaluator'.")
            else:
                print(f"  - OK: User '{email}' already has the 'evaluator' role.")

        except NotFoundError:
            # User does NOT exist, so we create them
            print(f"  - INFO: User '{email}' not found. Creating new evaluator account.")
            try:
                new_user = {
                    "email": email,
                    "hashed_password": hashed_password,
                    "full_name": email.split('@')[0], # Use a sensible default for the name
                    "birthday": "1900-01-01",
                    "role": "evaluator"
                }
                users_table.insert(new_user, pk='email')
                print(f"  - ✅ CREATED: New evaluator user '{email}' was created with a default password.")
            except Exception as e:
                print(f"  - ❌ ERROR: Failed to create new user '{email}': {e}")
        except Exception as e:
            print(f"  - ❌ ERROR: An unexpected error occurred for user '{email}': {e}")

    print("--- Role sync complete. ---")


if __name__ == "__main__":
    sync_evaluator_roles()