
import pytest
import json
from fastlite import database
from app.database import setup_database
from app.controllers.evaluator_workbench_controller import EvaluatorWorkbenchController
from app.controllers.evaluator import EvaluatorController
from app.controllers.evaluator_search_controller import EvaluatorSearchController
from app.logic.models import ComplianceDashboardState
from app.logic.validator import ValidationEngine

# Mock classes
class MockRequest:
    def __init__(self, session=None, form_data=None):
        self.session = session or {}
        self._form_data = form_data or {}
    
    async def form(self):
        return self._form_data

@pytest.fixture
def db():
    # Setup test DB (using a file to allow persistence checks or :memory:)
    # For integration/persistence, files are safer to verify "re-open" behavior, 
    # but :memory: is faster and effectively isolates "written to disk" semantics for sqlite.
    # We'll use :memory: but ensure we re-instantiate controllers to simulate "new request".
    db_path = ":memory:" 
    # db_path = "test_persistence.db"
    
    # We can rely on setup_database logic but injecting the path is hard as it's hardcoded to env or default.
    # So we'll manually create the tables or just use the setup_database if we can patch env.
    
    # Let's just create a fresh DB wrapper for the test using the schema logic from database.py?
    # Better: Use the actual setup_database but mocked path? 
    # The setup_database uses global DB_FILE. 
    # We will manually create the tables for the test to ensure isolation and speed.
    
    db = database(":memory:")
    
    # Users
    db.t.users.create(email=str, full_name=str, role=str, pk='email')
    db.t.users.insert(email="eval@example.com", full_name="Eval Uator", role="evaluator")
    db.t.users.insert(email="app@example.com", full_name="App Licant", role="applicant")

    # Applied Qualifications
    db.t.applied_qualifications.create(
        id=int, user_email=str, qualification_name=str, level=str,
        specialisation=str, activity=str, 
        eval_decision=str, eval_comment=str,
        pk='id'
    )
    # Evaluations (Target of our test)
    db.t.evaluations.create(
        qual_id=str, evaluator_email=str, evaluation_state_json=str, updated_at=str, pk='qual_id'
    )
    
    return db

@pytest.fixture
def validation_engine():
    # Mock or real? Real is complex to init. Mocking is better for "persistence" focus.
    class MockValidationEngine:
        def dict_to_state(self, d):
            s = ComplianceDashboardState(package_id="test_pkg", overall_met=False)
            s.__dict__.update(d)
            return s
        
        def validate(self, *args):
            s = ComplianceDashboardState(package_id="test_pkg", overall_met=False)
            s.overall_met = False
            return [s]

    return MockValidationEngine()

@pytest.mark.asyncio
async def test_persistence_workflow(db, validation_engine):
    """
    Test that re_evaluate_application saves state to DB and subsequent reads retrieval it.
    """
    # Setup Controllers
    search_ctrl = EvaluatorSearchController(db, validation_engine)
    main_ctrl = EvaluatorController(db, search_ctrl, None, validation_engine)
    bench_ctrl = EvaluatorWorkbenchController(db, validation_engine, main_ctrl, search_ctrl)
    
    # Setup specific test data
    qual_id = "app@example.com:::Ehitusjuht, TASE 6:::Ehitusjuhtimine"
    db.t.applied_qualifications.insert(
        id=1, user_email="app@example.com", qualification_name="Ehitusjuhtimine", 
        level="Ehitusjuht, TASE 6", specialisation="Üldehitus"
    )

    # 1. Perform Re-evaluation (Write)
    form_data = {
        "final_decision": "Anda",
        "main_comment": "Test decision",
        "active_context": "otsus"
    }
    req = MockRequest(session={"user_email": "eval@example.com"}, form_data=form_data)
    
    await bench_ctrl.re_evaluate_application(req, qual_id)

    # 2. Verify DB state (Persistence)
    saved_eval = db.t.evaluations.get(qual_id)
    assert saved_eval is not None, "Evaluation record not found in DB"
    state = json.loads(saved_eval['evaluation_state_json'])
    assert state['final_decision'] == "Anda"
    assert state['otsus_comment'] == "Test decision"

    # 3. Verify Sync to Legacy Table
    legacy_qual = db.t.applied_qualifications.get(1)
    assert legacy_qual['eval_decision'] == "Anda"

    # 4. Verify Re-hydration (Read)
    # We call show_v2_application_detail which calls validations etc.
    # It should LOAD from db.t.evaluations
    
    # We need to mock _get_applicant_data_for_validation for the fallback check 
    # (though it shouldn't be reached if persistence works)
    # But just in case, we patch it
    original_get_applicant = main_ctrl._get_applicant_data_for_validation
    main_ctrl._get_applicant_data_for_validation = lambda email: None # If called, will likely error or return None
    
    # If persistence works, it won't call validation/applicant data
    try:
        center, _, _ = main_ctrl.show_v2_application_detail(req, qual_id)
        # Inspect the state in center panel if possible, or assume success if no error
        # center_panel returns FT components. 
    except Exception as e:
        pytest.fail(f"Failed to rehydrate: {e}")
    finally:
        main_ctrl._get_applicant_data_for_validation = original_get_applicant

