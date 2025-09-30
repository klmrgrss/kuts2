# promote_user.py
import sys
import os
from pathlib import Path

# --- Setup Project Path ---
# This allows the script to find modules in the 'app' directory
APP_PATH = Path(__file__).parent / 'app'
if str(APP_PATH) not in sys.path:
    sys.path.insert(0, str(APP_PATH))
# --- End Setup ---

from database import setup_database
from utils.email_sender import send_role_change_notification
from fastlite import NotFoundError

def promote_user(email: str, role: str):
    """
    Updates a user's role in the database and sends a notification email.
    """
    VALID_ROLES = ['applicant', 'evaluator', 'admin']
    if role not in VALID_ROLES:
        print(f"Error: Invalid role '{role}'. Please use one of: {', '.join(VALID_ROLES)}")
        return

    print(f"Connecting to the database...")
    db = setup_database()
    users_table = db.t.users
    
    try:
        user = users_table[email]
        
        if user['role'] == role:
            print(f"User '{email}' already has the role '{role}'. No changes made.")
            return
        
        # --- THE FIX: Use 'email=email' instead of 'pk=email' ---
        users_table.update({"role": role}, email=email)
        print(f"✅ Successfully updated role for '{email}' to '{role}'.")

        # Send email notification
        send_role_change_notification(user_email=email, user_name=user['full_name'], new_role=role)

    except NotFoundError:
        print(f"Error: User with email '{email}' not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python promote_user.py <user_email> <new_role>")
        print("Example: python promote_user.py evaluator@example.com evaluator")
        sys.exit(1)
    
    user_email_arg = sys.argv[1]
    new_role_arg = sys.argv[2]
    
    promote_user(user_email_arg, new_role_arg)