# app/controllers/evaluator_workbench_controller.py

from fasthtml.common import *
from starlette.requests import Request
from fastlite import NotFoundError
import json
import datetime
import traceback
import dataclasses
from logic.validator import ValidationEngine
from logic.models import ApplicantData, ComplianceDashboardState
from ui.evaluator_v2.center_panel import render_compliance_dashboard

QUALIFICATION_LEVEL_TO_RULE_ID = {
    "Ehituse tööjuht, TASE 5": "toojuht_tase_5",
    "Ehitusjuht, TASE 6": "ehitusjuht_tase_6",
}

class EvaluatorWorkbenchController:
    def __init__(self, db, validation_engine, main_controller):
        self.db = db
        self.evaluations_table = db.t.evaluations
        self.validation_engine = validation_engine
        self.main_controller = main_controller # Reference to the main controller

    async def re_evaluate_application(self, request: Request, qual_id: str):
        print("\n--- [DEBUG] ENTERING RE-EVALUATION ENDPOINT ---")
        try:
            user_email, level, activity = qual_id.split('-', 2)
            form_data = await request.form()
            
            print(f"--- [DEBUG] Raw form data received: {form_data}")

            selected_education = form_data.get("education_level") or "any"
            is_old_or_foreign = form_data.get("education_old_or_foreign") == "on"
            
            print(f"--- [DEBUG] Evaluator selected education: '{selected_education}', Old/Foreign: {is_old_or_foreign}")

            applicant_data = self.main_controller._get_applicant_data_for_validation(user_email)
            applicant_data.education = selected_education
            applicant_data.is_education_old_or_foreign = is_old_or_foreign
            
            print(f"--- [DEBUG] ApplicantData object for validation: {applicant_data}")

            qualification_rule_id = QUALIFICATION_LEVEL_TO_RULE_ID.get(level, "toojuht_tase_5")
            all_states = self.validation_engine.validate(applicant_data, qualification_rule_id)
            best_state = next((s for s in all_states if s.overall_met), all_states[0])
            print(f"--- [DEBUG] Best validation state: Package '{best_state.package_id}', Met: {best_state.overall_met}")

            self._save_evaluation_state(qual_id, request.session.get("user_email"), best_state)
            
            return render_compliance_dashboard(best_state)

        except Exception as e:
            print(f"--- [ERROR] Re-evaluation failed: {e} ---")
            traceback.print_exc()
            return Div(f"An error occurred during re-evaluation: {e}", cls="p-4 text-red-500")

    def _save_evaluation_state(self, qual_id: str, evaluator_email: str, state: ComplianceDashboardState):
        try:
            state_dict = dataclasses.asdict(state)
            
            try:
                self.evaluations_table.get(qual_id)
                self.evaluations_table.update({
                    "evaluation_state_json": json.dumps(state_dict),
                    "updated_at": str(datetime.datetime.now())
                }, pk_values=qual_id)
                print(f"--- [DEBUG] Updated evaluation state for {qual_id}")
            except NotFoundError:
                self.evaluations_table.insert({
                    "qual_id": qual_id,
                    "evaluator_email": evaluator_email,
                    "evaluation_state_json": json.dumps(state_dict)
                }, pk='qual_id')
                print(f"--- [DEBUG] Inserted new evaluation state for {qual_id}")

        except Exception as db_error:
            print(f"--- [ERROR] Failed to save evaluation state for {qual_id}: {db_error}")