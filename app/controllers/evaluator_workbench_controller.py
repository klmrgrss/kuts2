# app/controllers/evaluator_workbench_controller.py

from fasthtml.common import *
from starlette.requests import Request
from fastlite import NotFoundError
import json
import re
import datetime
from fasthtml.common import *
from starlette.requests import Request
from fastlite import NotFoundError
import json
import traceback
import dataclasses
from logic.validator import ValidationEngine
from logic.models import ApplicantData, ComplianceDashboardState
from ui.evaluator_v2.center_panel import render_compliance_dashboard
from ui.evaluator_v2.application_list import render_application_item, render_application_list
from utils.log import debug, error

QUALIFICATION_LEVEL_TO_RULE_ID = {
    "Ehituse tööjuht, TASE 5": "toojuht_tase_5",
    "Ehitusjuht, TASE 6": "ehitusjuht_tase_6",
    "toojuht_tase_5": "toojuht_tase_5",
    "ehitusjuht_tase_6": "ehitusjuht_tase_6",
}

def _calculate_years(start_str, end_str):
    if not start_str: return 0.0
    try:
        start = datetime.datetime.strptime(start_str, "%Y-%m").date()
        end = datetime.datetime.strptime(end_str, "%Y-%m").date() if end_str else datetime.date.today()
        diff_months = (end.year - start.year) * 12 + (end.month - start.month) + 1
        return max(0, diff_months / 12.0)
    except:
            return 0.0

class EvaluatorWorkbenchController:
    def __init__(self, db, validation_engine, main_controller, search_controller):
        self.db = db
        self.evaluations_table = db.t.evaluations
        self.validation_engine = validation_engine
        self.main_controller = main_controller 
        self.search_controller = search_controller
        self.qual_table = db.t.applied_qualifications

    def _apply_accepted_experience_logic(self, state: ComplianceDashboardState, work_experience: list):
        if not work_experience: return

        # 1. Calculate Sum of Accepted Rows
        accepted_years = 0.0
        if state.accepted_work_experience_ids:
            for exp in work_experience:
                if exp.get('id') in state.accepted_work_experience_ids:
                    accepted_years += _calculate_years(exp.get('start_date'), exp.get('end_date'))
        
       # 2. Construct Header
        from logic.helpers import construct_workex_header
        
        # We pass the CURRENT provided string as the raw source. 
        # The helper parses out the previous number if it exists.
        current_prov = state.matching_experience.provided or "0a"
        
        new_header = construct_workex_header(
            state.matching_experience.required,
            current_prov,
            accepted_years
        )
        state.matching_experience.provided = new_header
        
        # 3. Color Logic (Overrule Validator)
        req_val = 0.0
        try:
             # Extract number from req string (e.g. "2 a" or "2")
             m = re.search(r'([\d\.]+)', state.matching_experience.required)
             if m: req_val = float(m.group(1))
        except: pass
        
        # Force the compliance status based on ACCEPTED amount
        state.matching_experience.is_met = accepted_years >= req_val

    async def toggle_work_experience(self, request: Request, qual_id: str, exp_id: int):
        try:
            exp_id = int(exp_id)
            user_email, level, activity = qual_id.split(':::', 2)
            
            # 1. Load State
            best_state = None
            rows = list(self.db.execute("SELECT evaluation_state_json FROM evaluations WHERE qual_id = ?", (qual_id,)))
            if rows:
                best_state = self.validation_engine.dict_to_state(json.loads(rows[0][0]))
            
            if not best_state:
                # FALLBACK: Generate fresh state if not found (First interaction workaround)
                # This mirrors the initial load logic in EvaluatorController to ensure continuity.
                qualification_rule_id = QUALIFICATION_LEVEL_TO_RULE_ID.get(level, "toojuht_tase_5")
                applicant_data = self.main_controller._get_applicant_data_for_validation(user_email, activity=activity)
                all_states = self.validation_engine.validate(applicant_data, qualification_rule_id)
                best_state = next((s for s in all_states if s.overall_met), all_states[0])
                
                # Hydrate Legacy Decision if exists (Safety measure to not overwrite decisions with None)
                # We use the raw table access for speed.
                uq_rows = list(self.db.t.applied_qualifications.rows_where("user_email = ? AND level = ? AND qualification_name = ?", [user_email, level, activity]))
                if uq_rows and uq_rows[0].get('eval_decision'):
                     best_state.final_decision = uq_rows[0].get('eval_decision')
                     if uq_rows[0].get('eval_comment'): 
                         best_state.otsus_comment = uq_rows[0].get('eval_comment')
                
                # debug(f"Generated fresh state on-the-fly for toggle: {qual_id}")

            # 2. Toggle ID
            if not hasattr(best_state, 'accepted_work_experience_ids'):
                best_state.accepted_work_experience_ids = []
            
            if exp_id in best_state.accepted_work_experience_ids:
                best_state.accepted_work_experience_ids.remove(exp_id)
            else:
                best_state.accepted_work_experience_ids.append(exp_id)
            
            # 3. Apply Logic with fresh data
            work_experience = list(self.db.t.work_experience.rows_where("user_email = ?", [user_email], order_by='start_date DESC'))
            self._apply_accepted_experience_logic(best_state, work_experience)

            # 4. Save
            self._save_evaluation_state(qual_id, user_email, best_state) # Note: session user might be different from applicant, but here we need evaluator email?
            # Re-read evaluator email from session?
            evaluator_email = request.session.get("user_email")
            self._save_evaluation_state(qual_id, evaluator_email, best_state)

            # 5. Render Dashboard
            # Pass qual_id and work_experience explicitly
            accepted_ids = best_state.accepted_work_experience_ids
            from ui.evaluator_v2.workex_table import render_work_experience_table
            
            # Since we only want to update the dashboard/center panel, we call render_compliance_dashboard
            # But wait, render_compliance_dashboard renders the WHOLE list of sections.
            # We assume toggle is done via OOB or simple replacement.
            # The UI asks for hx_target="#compliance-dashboard-container"
            dashboard = render_compliance_dashboard(best_state, work_experience=work_experience, qual_id=qual_id)
            
            return dashboard

        except Exception as e:
            traceback.print_exc()
            return Div(f"Error: {e}", cls="text-red-500")

    async def re_evaluate_application(self, request: Request, qual_id: str):
        print("\n--- [DEBUG] ENTERING RE-EVALUATION ENDPOINT ---")
        try:
            user_email, level, activity = qual_id.split(':::', 2)
            form_data = await request.form()
            
            debug(f"Raw form data received: {form_data}")

            # 1. Restore previous state using raw SQL
            best_state = None
            try:
                rows = list(self.db.execute("SELECT evaluation_state_json FROM evaluations WHERE qual_id = ?", (qual_id,)))
                if rows:
                    evaluation_state_json = rows[0][0]
                    saved_state_data = json.loads(evaluation_state_json)
                    best_state = self.validation_engine.dict_to_state(saved_state_data)
                    debug(f"Loaded previous state for {qual_id}")
            except Exception as e:
                debug(f"Could not load previous state for {qual_id}: {e} ({type(e).__name__})")

            if best_state is None:
                # FALLBACK: Generate fresh state if not found (First interaction workaround)
                # This mirrors the initial load logic in EvaluatorController to ensure continuity.
                qualification_rule_id = QUALIFICATION_LEVEL_TO_RULE_ID.get(level, "toojuht_tase_5")
                applicant_data = self.main_controller._get_applicant_data_for_validation(user_email, activity=activity)
                all_states = self.validation_engine.validate(applicant_data, qualification_rule_id)
                best_state = next((s for s in all_states if s.overall_met), all_states[0])
                debug(f"Created fresh state for {qual_id}")

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
                debug(f"[ACTION] Override changed for {qual_id}: Education '{current_edu}'->'{selected_education}', Foreign: {current_old_foreign}->{is_old_or_foreign}")
                # Re-run validation with the new override
                applicant_data = self.main_controller._get_applicant_data_for_validation(user_email, activity=activity)
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

                # Preserve carry-over data (comments and decisions AND accepted_ids)
                new_best_state.haridus_comment = best_state.haridus_comment
                new_best_state.tookogemus_comment = best_state.tookogemus_comment
                new_best_state.koolitus_comment = best_state.koolitus_comment
                new_best_state.otsus_comment = best_state.otsus_comment
                new_best_state.final_decision = best_state.final_decision
                # Preserve accepted IDs
                if hasattr(best_state, 'accepted_work_experience_ids'):
                    new_best_state.accepted_work_experience_ids = best_state.accepted_work_experience_ids

                best_state = new_best_state
            
            # 4. Update the active context's comment if provided
            if active_context and comment is not None:
                comment_field_name = f"{active_context}_comment"
                if hasattr(best_state, comment_field_name):
                    setattr(best_state, comment_field_name, comment)
                    debug(f"[ACTION] Comment added to '{active_context}' (DB field: {comment_field_name}): \"{comment}\"")

            # 5. Update final decision if provided
            if final_decision is not None:
                best_state.final_decision = final_decision or None
                debug(f"[ACTION] Decision made: \"{best_state.final_decision}\"")

            # 6. Apply Accepted Experience Logic (Recalculate Totals/Status)
            work_experience = list(self.db.t.work_experience.rows_where("user_email = ?", [user_email], order_by='start_date DESC'))
            self._apply_accepted_experience_logic(best_state, work_experience)

            # 7. Final Sync & Save
            self._save_evaluation_state(qual_id, request.session.get("user_email"), best_state)
            
            # Pass qual_id to ensure checkboxes are clickable
            dashboard = render_compliance_dashboard(best_state, work_experience=work_experience, qual_id=qual_id)
            
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
            
            # Use raw SQL for robust INSERT OR REPLACE
            sql = """
                INSERT OR REPLACE INTO evaluations 
                (qual_id, evaluator_email, evaluation_state_json, updated_at) 
                VALUES (?, ?, ?, ?)
            """
            self.db.execute(sql, (
                qual_id, 
                evaluator_email, 
                json.dumps(state_dict), 
                str(datetime.datetime.now())
            ))

            # 2. Sync to applied_qualifications (Legacy/Robustness)
            # This ensures that even if the JSON state acts up, the core decision is preserved in the main table.
            try:
                user_email, level, activity = qual_id.split(':::', 2)
                decision = state.final_decision
                comment = state.otsus_comment
                
                sql_update = """
                    UPDATE applied_qualifications 
                    SET eval_decision = ?, eval_comment = ? 
                    WHERE user_email = ? AND level = ? AND qualification_name = ?
                """
                self.db.execute(sql_update, (decision, comment, user_email, level, activity))
                print(f"--- [DEBUG] Synced decision '{decision}' to applied_qualifications for {qual_id}")
            except Exception as sync_err:
                print(f"--- [WARN] Failed to sync to applied_qualifications: {sync_err}")

        except Exception as db_error:
            print(f"--- [ERROR] Failed to save evaluation state for {qual_id}: {db_error}")