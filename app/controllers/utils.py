# gem/controllers/utils.py

def get_badge_counts(db, user_email: str) -> dict:
    """
    Fetches counts or status for items to be displayed as badges on navigation tabs.

    Args:
        db: The fastlite database connection object.
        user_email: The email of the current user.

    Returns:
        A dictionary where keys are tab IDs (e.g., 'tookogemus') and values
        are the counts or status indicators (e.g., checkmark).
        Only includes keys where the count > 0 or status is relevant.
    """
    if not user_email:
        return {}

    badge_counts = {}

    # --- Work Experience Count ---
    try:
        # Use the efficient filtering pattern
        exp_table = db.t.work_experience
        all_experiences = exp_table(order_by='id') # Consider optimizing if many records
        user_experiences = [exp for exp in all_experiences if exp.get('user_email') == user_email]
        count = len(user_experiences)
        if count > 0:
            badge_counts['tookogemus'] = count
            print(f"--- DEBUG [get_badge_counts]: Work Experience Count for {user_email}: {count} ---")
    except Exception as e:
        print(f"--- ERROR calculating work experience badge count for {user_email}: {e} ---")

    # --- TODO: Add other badge calculations here in the future ---
    # Example: Qualification Count (count distinct qualification_name)
    # try:
    #     qual_table = db.t.applied_qualifications
    #     all_quals = qual_table(order_by='id')
    #     user_quals = [q for q in all_quals if q.get('user_email') == user_email]
    #     # Count unique activities/categories selected
    #     qual_count = len(set(q.get('qualification_name') for q in user_quals))
    #     if qual_count > 0:
    #         badge_counts['kutsed'] = qual_count
    # except Exception as e:
    #     print(f"--- ERROR calculating qualifications badge count for {user_email}: {e} ---")

    # Example: Checkmark for Education (if record exists)
    # try:
    #     edu_table = db.t.education
    #     all_edu = edu_table(order_by='id')
    #     user_edu = [edu for edu in all_edu if edu.get('user_email') == user_email]
    #     if user_edu: # Check if list is not empty
    #         badge_counts['haridus'] = "✓" # Or use a specific icon class name
    # except Exception as e:
    #     print(f"--- ERROR calculating education badge status for {user_email}: {e} ---")

    # Example: Checkmark for Training Files (if count > 0)
    # Example: Checkmark for Employment Proof (if record exists)

    print(f"--- DEBUG [get_badge_counts]: Final counts for {user_email}: {badge_counts} ---")
    return badge_counts