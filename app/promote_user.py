# app/promote_user.py
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# --- Setup Project Path ---
APP_PATH = Path(__file__).parent / 'app'
if str(APP_PATH) not in sys.path:
    sys.path.insert(0, str(APP_PATH))
# --- End Setup ---

# Load environment variables from .env file
load_dotenv()

from database import setup_database
from utils.email_sender import send_role_change_notification
from fastlite import NotFoundError

def sync_evaluator_roles():
    """
    Reads a list of evaluator emails from the environment variable 'EVALUATOR_EMAILS'
    and updates their roles in the database to 'evaluator'.
    """
    evaluator_emails_str = os.getenv("EVALUATOR_EMAILS")

    if not evaluator_emails_str:
        print("INFO: No EVALUATOR_EMAILS environment variable set. Nothing to sync.")
        return

    evaluator_emails = [email.strip() for email in evaluator_emails_str.split(',') if email.strip()]
    if not evaluator_emails:
        print("INFO: EVALUATOR_EMAILS variable is empty. Nothing to sync.")
        return

    print(f"--- Starting role sync for {len(evaluator_emails)} designated evaluators... ---")
    
    print("Connecting to the database...")
    db = setup_database()
    users_table = db.t.users

    for email in evaluator_emails:
        try:
            user = users_table[email]
            
            if user['role'] == 'evaluator':
                print(f"  - OK: User '{email}' already has the 'evaluator' role.")
                continue
            
            # Update the user's role
            users_table.update({"role": "evaluator"}, pk=email)
            print(f"  - ✅ SUCCESS: Promoted user '{email}' to 'evaluator'.")

            # Optionally send a notification email
            # send_role_change_notification(user_email=email, user_name=user['full_name'], new_role='evaluator')

        except NotFoundError:
            print(f"  - ⚠️ WARNING: User with email '{email}' not found in the database. Please ensure they are registered.")
        except Exception as e:
            print(f"  - ❌ ERROR: An unexpected error occurred for user '{email}': {e}")

    print("--- Role sync complete. ---")


if __name__ == "__main__":
    sync_evaluator_roles()