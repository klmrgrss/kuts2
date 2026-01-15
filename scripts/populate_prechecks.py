import json
import dataclasses
from pathlib import Path
import sys
import os
import datetime

# Ensure app is in path
APP_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app'))
sys.path.insert(0, APP_PATH)

from logic.validator import ValidationEngine
from logic.models import ApplicantData
from fastlite import database

QUALIFICATION_LEVEL_TO_RULE_ID = {
    "Ehituse tööjuht, TASE 5": "toojuht_tase_5",
    "Ehitusjuht, TASE 6": "ehitusjuht_tase_6",
}

def run_proactive_prechecks():
    db_path = "/home/kalmerg/eeel/kuts2/data/app.db"
    db = database(db_path)
    rules_path = Path(APP_PATH) / 'config' / 'rules.toml'
    engine = ValidationEngine(rules_path)
    
    apps = db.t.applied_qualifications()
    print(f"Checking {len(apps)} applications...")

    for app in apps:
        user_email = app.get('user_email')
        level = app.get('level')
        activity = app.get('qualification_name')
        qual_id = f"{user_email}:::{level}:::{activity}"
        
        # Simple check if already exists
        try:
            db.t.evaluations.get(qual_id)
            # print(f"Skipping {qual_id}, already exists.")
            continue
        except: pass

        print(f"Processing {qual_id}...")
        
        # Mock applicant data for precheck (since we don't have full data fetcher here)
        # We try to guess based on user email or just use defaults
        edu = "any"
        if "pass" in user_email: edu = "vastav_kõrgharidus_300_eap"
        
        applicant_data = ApplicantData(
            education=edu,
            work_experience_years=5.0,
            matching_experience_years=3.0,
            has_prior_level_4=True, base_training_hours=40
        )
        
        rule_id = QUALIFICATION_LEVEL_TO_RULE_ID.get(level, "toojuht_tase_5")
        states = engine.validate(applicant_data, rule_id)
        best_state = states[0]
        
        state_dict = dataclasses.asdict(best_state)
        db.t.evaluations.insert({
            "qual_id": qual_id,
            "evaluator_email": "system@auto.precheck",
            "evaluation_state_json": json.dumps(state_dict)
        }, pk="qual_id")

    print("Done.")

if __name__ == "__main__":
    run_proactive_prechecks()
