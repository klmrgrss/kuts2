
import pytest
import json
import datetime
from fastlite import database
from app.controllers.evaluator_workbench_controller import EvaluatorWorkbenchController
from app.controllers.evaluator import EvaluatorController
from app.controllers.evaluator_search_controller import EvaluatorSearchController
from app.logic.models import ComplianceDashboardState, ComplianceCheck
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
    db = database(":memory:")
    
    # Users
    db.t.users.create(email=str, full_name=str, role=str, pk='email')
    db.t.users.insert(email="eval@example.com", full_name="Eval Uator", role="evaluator")
    db.t.users.insert(email="app@example.com", full_name="App Licant", role="applicant")

    # Work Experience
    db.t.work_experience.create(
        id=int, user_email=str, start_date=str, end_date=str, role=str, pk='id'
    )
    # Insert 2 experiences
    # Exp 1: 1 year (2020-01 to 2020-12)
    db.t.work_experience.insert(id=101, user_email="app@example.com", start_date="2020-01", end_date="2020-12", role="Role 1")
    # Exp 2: 2 years (2021-01 to 2022-12)
    db.t.work_experience.insert(id=102, user_email="app@example.com", start_date="2021-01", end_date="2022-12", role="Role 2")

    # Evaluations
    db.t.evaluations.create(
        qual_id=str, evaluator_email=str, evaluation_state_json=str, updated_at=str, pk='qual_id'
    )
    
    # Applied Qualifications
    db.t.applied_qualifications.create(
         id=int, user_email=str, qualification_name=str, level=str, activity=str, 
         eval_decision=str, eval_comment=str, pk='id'
    )

    return db

@pytest.fixture
def validation_engine():
    class MockValidationEngine:
        def dict_to_state(self, d):
            s = ComplianceDashboardState(package_id="test_pkg", overall_met=False)
            s.matching_experience = ComplianceCheck(required="2a", provided="Esitatud: 3a")
            
            for k, v in d.items():
                if k == 'matching_experience' and isinstance(v, dict):
                    # Filter keys to match dataclass fields to avoid unexpected args
                    valid_keys = ComplianceCheck.__dataclass_fields__.keys()
                    safe_v = {sk: sv for sk, sv in v.items() if sk in valid_keys}
                    setattr(s, k, ComplianceCheck(**safe_v))
                else:
                    if hasattr(s, k):
                        setattr(s, k, v)
            
            if not getattr(s, 'accepted_work_experience_ids', None):
                s.accepted_work_experience_ids = []
            return s
        
        def validate(self, *args):
            s = ComplianceDashboardState(package_id="test_pkg", overall_met=False)
            s.matching_experience = ComplianceCheck(required="2a", provided="Esitatud: 3a")
            s.overall_met = False
            return [s]

    return MockValidationEngine()

@pytest.mark.asyncio
async def test_toggle_experience_logic(db, validation_engine):
    # Setup
    search_ctrl = EvaluatorSearchController(db, validation_engine)
    main_ctrl = EvaluatorController(db, search_ctrl, None, validation_engine)
    bench_ctrl = EvaluatorWorkbenchController(db, validation_engine, main_ctrl, search_ctrl)
    
    qual_id = "app@example.com:::Ehitusjuht, TASE 6:::Ehitusjuhtimine"
    req = MockRequest(session={"user_email": "eval@example.com"})

    # 1. Initial State (No acceptance)
    # This should create the default state
    await bench_ctrl.re_evaluate_application(req, qual_id)
    
    saved = db.t.evaluations.get(qual_id)
    state = json.loads(saved['evaluation_state_json'])
    assert state['accepted_work_experience_ids'] == []
    # Check text
    # Check text
    assert "Vastavaks tunnistatud: 0a 0k" in state['matching_experience']['provided']
    # 0 < 2a required, so is_met should be False
    assert state['matching_experience']['is_met'] == False

    # 2. Toggle ID 102 (2 years) -> Accepted
    # This should satisfy the 2a requirement
    await bench_ctrl.toggle_work_experience(req, qual_id, 102)
    
    saved = db.t.evaluations.get(qual_id)
    state = json.loads(saved['evaluation_state_json'])
    assert 102 in state['accepted_work_experience_ids']
    assert 101 not in state['accepted_work_experience_ids']
    
    # Check logic
    # Role 2 is 2 years. Accepted should be 2a 0k
    assert "Vastavaks tunnistatud: 2a" in state['matching_experience']['provided']
    assert state['matching_experience']['is_met'] == True # 2 >= 2

    # 3. Toggle ID 101 (1 year) -> Accepted (Total 3 years)
    await bench_ctrl.toggle_work_experience(req, qual_id, 101)
    
    saved = db.t.evaluations.get(qual_id)
    state = json.loads(saved['evaluation_state_json'])
    assert 101 in state['accepted_work_experience_ids']
    assert 102 in state['accepted_work_experience_ids']
    assert "Vastavaks tunnistatud: 3a" in state['matching_experience']['provided']

    # 4. Toggle ID 102 OFF -> Total 1 year (Not met)
    await bench_ctrl.toggle_work_experience(req, qual_id, 102)
    
    saved = db.t.evaluations.get(qual_id)
    state = json.loads(saved['evaluation_state_json'])
    assert 102 not in state['accepted_work_experience_ids']
    assert 101 in state['accepted_work_experience_ids']
    assert "Vastavaks tunnistatud: 1a" in state['matching_experience']['provided']
    assert state['matching_experience']['is_met'] == False

