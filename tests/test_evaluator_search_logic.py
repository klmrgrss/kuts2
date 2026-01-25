
import pytest
from app.controllers.evaluator_search_controller import EvaluatorSearchController
from fastlite import database

@pytest.fixture
def db():
    db = database(":memory:")
    # Users
    db.t.users.create(email=str, full_name=str, pk='email')
    db.t.users.insert(email="user1@example.com", full_name="User One")
    db.t.users.insert(email="user2@example.com", full_name="User Two")

    # Applied Qualifications
    # We purposefully set different decisions in the legacy storage to test the bug
    db.t.applied_qualifications.create(
        id=int, user_email=str, qualification_name=str, level=str,
        specialisation=str, activity=str, 
        eval_decision=str,
        pk='id'
    )
    
    # User 1: REJECTED
    db.t.applied_qualifications.insert(
        id=1, user_email="user1@example.com", 
        level="Lvl5", qualification_name="Job", specialisation="Spec1",
        eval_decision="Mitte anda"
    )
    
    # User 2: APPROVED
    db.t.applied_qualifications.insert(
        id=2, user_email="user2@example.com", 
        level="Lvl5", qualification_name="Job", specialisation="Spec1",
        eval_decision="Anda"
    )
    
    # Empty evaluations table (force fallback to applied_qualifications)
    db.t.evaluations.create(
        qual_id=str, evaluation_state_json=str, pk='qual_id'
    )
    
    return db

def test_flattened_application_logic_bug(db):
    """
    Expose variable scope bug where loop variable 'qual' leaks 
    and applies one user's decision to another.
    """
    ctrl = EvaluatorSearchController(db, None)
    
    apps = ctrl._get_flattened_applications()
    
    # Sort to ensure consistent checking
    apps.sort(key=lambda x: x['applicant_name'])
    
    user1_app = next(a for a in apps if a['applicant_name'] == "User One")
    user2_app = next(a for a in apps if a['applicant_name'] == "User Two")
    
    print(f"User 1 Decision: {user1_app['final_decision']}")
    print(f"User 2 Decision: {user2_app['final_decision']}")
    
    assert user1_app['final_decision'] == "Mitte anda", f"User 1 should be 'Mitte anda', got '{user1_app['final_decision']}'"
    assert user2_app['final_decision'] == "Anda", f"User 2 should be 'Anda', got '{user2_app['final_decision']}'"
