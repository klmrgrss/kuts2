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

            # --- Restore previous state or create a new one ---
            try:
                saved_evaluation = self.evaluations_table.get(qual_id)
                saved_state_data = json.loads(saved_evaluation['evaluation_state_json'])
                best_state = self.validation_engine.dict_to_state(saved_state_data)
                print(f"--- [DEBUG] Loaded existing evaluation state for {qual_id}")
            except (NotFoundError, json.JSONDecodeError):
                best_state = None # Will trigger re-validation later
                print(f"--- [DEBUG] No existing state found for {qual_id}. Will create new.")

            # --- Get evaluator input from form ---
            selected_education = form_data.get("education_level")
            is_old_or_foreign = form_data.get("education_old_or_foreign") == "on"
            comment = form_data.get("main_comment")
            active_context = form_data.get("active_context")
            final_decision = form_data.get("final_decision")

            print(
                f"--- [DEBUG] Evaluator Inputs: Education='{selected_education}', Old/Foreign={is_old_or_foreign}, "
                f"Final decision='{final_decision}', Context='{active_context}' ---"
            )
            
            # --- Get base applicant data ---
            applicant_data = self.main_controller._get_applicant_data_for_validation(user_email)
            
            # --- If state has changed, re-run validation ---
            # A change is defined as a new education selection or a change in the old/foreign flag.
            has_state_changed = (best_state is None) or \
                                (selected_education is not None and applicant_data.education != selected_education) or \
                                (applicant_data.is_education_old_or_foreign != is_old_or_foreign)

            if has_state_changed:
                print("--- [DEBUG] State has changed. Re-running full validation.")
                applicant_data.education = selected_education or "any"
                applicant_data.is_education_old_or_foreign = is_old_or_foreign

                qualification_rule_id = QUALIFICATION_LEVEL_TO_RULE_ID.get(level, "toojuht_tase_5")
                all_states = self.validation_engine.validate(applicant_data, qualification_rule_id)
                new_best_state = next((s for s in all_states if s.overall_met), all_states[0])

                # Preserve comments from the old state if it existed
                if best_state:
                    new_best_state.haridus_comment = best_state.haridus_comment
                    new_best_state.tookogemus_comment = best_state.tookogemus_comment
                    new_best_state.koolitus_comment = best_state.koolitus_comment
                    new_best_state.otsus_comment = best_state.otsus_comment
                    new_best_state.final_decision = getattr(best_state, "final_decision", None)

                best_state = new_best_state
                print(f"--- [DEBUG] New best validation state: Package '{best_state.package_id}', Met: {best_state.overall_met}")
            else:
                print("--- [DEBUG] State has not changed. Only updating comments.")

            if best_state:
                if selected_education is not None and hasattr(best_state, "education"):
                    best_state.education.provided = selected_education or best_state.education.provided
                best_state.education_old_or_foreign = is_old_or_foreign
                best_state.final_decision = final_decision or None

            # --- Update comments based on active context ---
            if active_context and comment is not None:
                comment_field_name = f"{active_context}_comment"
                if hasattr(best_state, comment_field_name):
                    setattr(best_state, comment_field_name, comment)
                    print(f"--- [DEBUG] Updated comment for '{active_context}': '{comment[:30]}...'")

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