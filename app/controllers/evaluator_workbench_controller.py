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
from ui.evaluator_v2.application_list import render_application_item, render_application_list

QUALIFICATION_LEVEL_TO_RULE_ID = {
    "Ehituse tööjuht, TASE 5": "toojuht_tase_5",
    "Ehitusjuht, TASE 6": "ehitusjuht_tase_6",
    "toojuht_tase_5": "toojuht_tase_5",
    "ehitusjuht_tase_6": "ehitusjuht_tase_6",
}

class EvaluatorWorkbenchController:
    def __init__(self, db, validation_engine, main_controller, search_controller):
        self.db = db
        self.evaluations_table = db.t.evaluations
        self.validation_engine = validation_engine
        self.main_controller = main_controller 
        self.search_controller = search_controller

    async def re_evaluate_application(self, request: Request, qual_id: str):
        print("\n--- [DEBUG] ENTERING RE-EVALUATION ENDPOINT ---")
        try:
            user_email, level, activity = qual_id.split(':::', 2)
            form_data = await request.form()
            
            print(f"--- [DEBUG] Raw form data received: {form_data}")

            # 1. Restore previous state
            best_state = None
            try:
                saved_evaluation = self.evaluations_table.get(qual_id)
                if saved_evaluation:
                    saved_state_data = json.loads(saved_evaluation['evaluation_state_json'])
                    best_state = self.validation_engine.dict_to_state(saved_state_data)
                    print(f"--- [DEBUG] Loaded previous state for {qual_id} ---")
            except Exception as e:
                print(f"--- [WARN] Could not load previous state for {qual_id}: {e} ---")

            if best_state is None:
                # If no state, perform initial validation
                applicant_data = self.main_controller._get_applicant_data_for_validation(user_email)
                qualification_rule_id = QUALIFICATION_LEVEL_TO_RULE_ID.get(level, "toojuht_tase_5")
                all_states = self.validation_engine.validate(applicant_data, qualification_rule_id)
                best_state = next((s for s in all_states if s.overall_met), all_states[0])
                print(f"--- [DEBUG] Created fresh state for {qual_id} ---")

            # 2. Get evaluator inputs from form
            selected_education = form_data.get("education_level")
            is_old_or_foreign = form_data.get("education_old_or_foreign") == "on"
            comment = form_data.get("main_comment")
            active_context = form_data.get("active_context")
            final_decision = form_data.get("final_decision")

            # 3. Detect changes in overrides
            # Compare current form values with what's in the state (not original applicant data)
            current_edu = best_state.education.provided if best_state.education else "any"
            current_old_foreign = bool(best_state.education_old_or_foreign)

            # If selected_education is empty string (from dropdown), we interpret it as a specific choice
            # but we need to check if it has changed from the CURRENT state.
            has_override_changed = (selected_education is not None and selected_education != current_edu) or \
                                   (is_old_or_foreign != current_old_foreign)

            if has_override_changed:
                print(f"--- [DEBUG] Override changed: {current_edu} -> {selected_education}")
                # Re-run validation with the new override
                applicant_data = self.main_controller._get_applicant_data_for_validation(user_email)
                if selected_education is not None:
                    applicant_data.education = selected_education or "any"
                applicant_data.is_education_old_or_foreign = is_old_or_foreign

                qualification_rule_id = QUALIFICATION_LEVEL_TO_RULE_ID.get(level, "toojuht_tase_5")
                all_states = self.validation_engine.validate(applicant_data, qualification_rule_id)
                
                # Sorter: Prioritize states that match the criteria better
                # 1. Overall Met
                # 2. Has Education Requirement (if we just changed education)
                def state_sort_key(s):
                    # We want overall_met=True first
                    score = 0
                    if s.overall_met: score += 100
                    if s.education.is_relevant: score += 1
                    return score

                sorted_states = sorted(all_states, key=state_sort_key, reverse=True)
                new_best_state = sorted_states[0]

                # Preserve carry-over data (comments and decisions)
                new_best_state.haridus_comment = best_state.haridus_comment
                new_best_state.tookogemus_comment = best_state.tookogemus_comment
                new_best_state.koolitus_comment = best_state.koolitus_comment
                new_best_state.otsus_comment = best_state.otsus_comment
                new_best_state.final_decision = best_state.final_decision

                best_state = new_best_state
            
            # 4. Update the active context's comment if provided
            if active_context and comment is not None:
                comment_field_name = f"{active_context}_comment"
                if hasattr(best_state, comment_field_name):
                    setattr(best_state, comment_field_name, comment)
                    print(f"--- [DEBUG] Updated comment for '{active_context}'")

            # 5. Update final decision if provided
            if final_decision is not None:
                best_state.final_decision = final_decision or None

            # 6. Final Sync & Save
            # 6. Final Sync & Save
            self._save_evaluation_state(qual_id, request.session.get("user_email"), best_state)
            
            dashboard = render_compliance_dashboard(best_state)
            
            # --- OOB update: Full Sidebar Refresh (Ensures consistency) ---
            # Fetch all applications to render the updated list
            # We pass the current 'best_state' as an override to ensure the list reflects the NEW decision immediately,
            # bypassing any potential DB commit/read latency.
            all_apps = self.search_controller._get_flattened_applications(
                override_eval_states={qual_id: best_state}
            )
            
            # 1. Desktop List Content
            desktop_list_content = render_application_list(all_apps, include_oob=False, active_qual_id=qual_id)
            
            # 2. Drawer List Content (Same content logic, effectively just regenerating the FT components)
            drawer_list_content = render_application_list(all_apps, include_oob=False, active_qual_id=qual_id)

            # Create OOB swaps for BOTH containers
            oob_swaps = (
                Div(desktop_list_content, id="application-list-container", hx_swap_oob="true"),
                Div(drawer_list_content, id="application-list-container-drawer", hx_swap_oob="true")
            )
            
            print(f"--- [DEBUG] OOB Update - Refreshing application lists ({len(all_apps)} items) with active: {qual_id}")
            
            return dashboard, *oob_swaps

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
            except NotFoundError:
                self.evaluations_table.insert({
                    "qual_id": qual_id,
                    "evaluator_email": evaluator_email,
                    "evaluation_state_json": json.dumps(state_dict)
                }, pk='qual_id')

        except Exception as db_error:
            print(f"--- [ERROR] Failed to save evaluation state for {qual_id}: {db_error}")