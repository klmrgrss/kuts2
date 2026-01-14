import json
import dataclasses
from pathlib import Path
import sys
import os

# Ensure app is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app')))

from logic.validator import ValidationEngine
from logic.models import ApplicantData, ComplianceDashboardState

def test_reproduction():
    rules_path = Path(__file__).parent.parent / 'app' / 'config' / 'rules.toml'
    engine = ValidationEngine(rules_path)
    
    # 1. Simulate an applicant with high education (Green)
    applicant = ApplicantData(
        education="vastav_kõrgharidus_300_eap", # Master's
        work_experience_years=5.0,
        matching_experience_years=5.0,
        base_training_hours=40
    )
    
    qual_id = "ehitusjuht_tase_6" # Assuming this ID exists in rules.toml
    states = engine.validate(applicant, qual_id)
    best_state = states[0]
    
    print(f"\nInitial State (High Ed):")
    print(f"Overall Met: {best_state.overall_met}")
    print(f"Education Met: {best_state.education.is_met}")
    
    # 2. Simulate Evaluator Override to lower education (Should turn Red)
    print("\nSimulating Override to 'keskharidus' (threshold is higher):")
    applicant.education = "keskharidus"
    new_states = engine.validate(applicant, qual_id)
    new_best_state = new_states[0]
    
    print(f"New State (Override):")
    print(f"Overall Met: {new_best_state.overall_met}")
    print(f"Education Met: {new_best_state.education.is_met}")
    
    if new_best_state.education.is_met:
        print("FAIL: Education still met after override to lower level!")
    else:
        print("SUCCESS: Education NOT met after override.")

    # 3. Test Serialization/Deserialization (Persistence)
    print("\nTesting Persistence (Serialization):")
    new_best_state.haridus_comment = "This is a test comment"
    state_dict = dataclasses.asdict(new_best_state)
    
    # Re-hydrate
    rehydrated = engine.dict_to_state(state_dict)
    print(f"Rehydrated Comment: {rehydrated.haridus_comment}")
    
    if rehydrated.haridus_comment == "This is a test comment":
        print("SUCCESS: Comment persisted through dict round-trip.")
    else:
        print("FAIL: Comment LOST during dict round-trip.")

if __name__ == "__main__":
    test_reproduction()
