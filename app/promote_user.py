"""Maintained entry point for synchronising default users.

The original deployment workflow executed this script to create evaluator
accounts.  The logic now lives in :mod:`auth.bootstrap` so that it can be shared
between the application start-up and this script.  Keeping the file means we do
not have to update any external automation immediately.
"""

import sys
from pathlib import Path

from dotenv import load_dotenv

# --- Setup Project Path ---
APP_PATH = Path(__file__).parent
if str(APP_PATH) not in sys.path:
    sys.path.insert(0, str(APP_PATH))
# --- End Setup ---

load_dotenv()

from database import setup_database  # noqa: E402  pylint: disable=wrong-import-position
from auth.bootstrap import ensure_default_users  # noqa: E402  pylint: disable=wrong-import-position


def main() -> None:
    print("--- Starting default user synchronisation ---")
    db = setup_database()
    ensure_default_users(db)
    print("--- Default user synchronisation complete ---")


if __name__ == "__main__":
    main()
