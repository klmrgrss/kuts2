import json
import sqlite3
import dataclasses
from pathlib import Path
import sys
import os

# Ensure app is in path
APP_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app'))
sys.path.insert(0, APP_PATH)

from logic.validator import ValidationEngine
from logic.models import ApplicantData
from controllers.evaluator_workbench_controller import EvaluatorWorkbenchController
from controllers.evaluator import EvaluatorController
from fastlite import database, NotFoundError

class MockRequest:
    def __init__(self, form_data, session):
        self._form_data = form_data
        self.session = session
    async def form(self):
        return self._form_data

def test_integration():
    db_path = "/home/kalmerg/eeel/kuts2/data/app.db"
    db = database(db_path)
    rules_path = Path(APP_PATH) / 'config' / 'rules.toml'
    engine = ValidationEngine(rules_path)
    
    # Setup controllers
    eval_controller = EvaluatorController(db, None, None, engine)
    workbench = EvaluatorWorkbenchController(db, engine, eval_controller)
    eval_controller.workbench_controller = workbench
    
    user_email = "test-user-dash@example.com"
    qual_id = f"{user_email}:::Ehitusjuht, TASE 6:::Üldehituslik ehitusjuhtimine"
    
    # 1. Clear previous state using raw SQL to avoid NotFoundError
    db.execute("DELETE FROM evaluations WHERE qual_id = ?", (qual_id,))
    db.execute("DELETE FROM education WHERE user_email = ?", (user_email,))
    print(f"Cleared state for {qual_id}")

    # 2. Add mock education data
    db.t.education.insert({
        "user_email": user_email,
        "education_category": "vastav_kõrgharidus_300_eap", # Master
        "institution": "Mock Uni"
    })

    # 3. Simulate re-evaluation with comment
    form = {
        "education_level": "vastav_kõrgharidus_300_eap", # Master
        "main_comment": "Initial comment",
        "active_context": "haridus"
    }
    request = MockRequest(form, {"user_email": "evaluator@test.com", "authenticated": True})
    
    import asyncio
    asyncio.run(workbench.re_evaluate_application(request, qual_id))
    print("Initial re-evaluation complete.")

    # 4. Verify persistence in DB
    record = db.t.evaluations.get(qual_id)
    state_data = json.loads(record['evaluation_state_json'])
    print(f"Saved Comment: {state_data.get('haridus_comment')}")
    
    # 5. Simulate override to LOW education (Should turn red)
    form_low = {
        "education_level": "keskharidus", # High School
        "active_context": "haridus",
        "main_comment": "Downgraded education"
    }
    request_low = MockRequest(form_low, {"user_email": "evaluator@test.com", "authenticated": True})
    
    async def run_low():
        await workbench.re_evaluate_application(request_low, qual_id)

    asyncio.run(run_low())
    
    record_new = db.t.evaluations.get(qual_id)
    state_new = json.loads(record_new['evaluation_state_json'])
    
    print(f"Selected Package: {state_new.get('package_id')}")
    edu_met = state_new['education']['is_met']
    print(f"Education Met after override to low: {edu_met}")
    print(f"Persisted Comment: {state_new.get('haridus_comment')}")

    # Cleanup
    db.execute("DELETE FROM evaluations WHERE qual_id = ?", (qual_id,))

    if not edu_met and state_new.get('haridus_comment') == "Downgraded education":
        print("\nALL TESTS PASSED: Override works and comment persisted!")
    else:
        print("\nTEST FAILED.")

if __name__ == "__main__":
    test_integration()
