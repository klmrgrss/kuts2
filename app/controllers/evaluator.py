# app/controllers/evaluator.py
from fasthtml.common import *
from starlette.requests import Request
from fastlite import NotFoundError
import datetime
import json
import re
import traceback
from logic.helpers import calculate_total_experience_years
from logic.models import ApplicantData, ComplianceDashboardState
from ui.evaluator_v2.ev_layout import ev_layout
from ui.evaluator_v2.left_panel import render_left_panel
from ui.evaluator_v2.center_panel import render_center_panel
from ui.evaluator_v2.right_panel import render_right_panel
from config.qualification_data import kt
from utils.log import debug, error


QUALIFICATION_LEVEL_TO_RULE_ID = {
    "Ehituse tööjuht, TASE 5": "toojuht_tase_5",
    "Ehitusjuht, TASE 6": "ehitusjuht_tase_6",
    # Slugs/IDs as well for robustness
    "toojuht_tase_5": "toojuht_tase_5",
    "ehitusjuht_tase_6": "ehitusjuht_tase_6",
}

class EvaluatorController:
    def __init__(self, db, search_controller, workbench_controller, validation_engine):
        self.db = db
        self.users_table = db.t.users
        self.qual_table = db.t.applied_qualifications
        self.work_exp_table = db.t.work_experience
        self.evaluations_table = db.t.evaluations
        self.search_controller = search_controller
        self.workbench_controller = workbench_controller
        self.validation_engine = validation_engine

    def show_dashboard_v2(self, request: Request):
        applications_data = self.search_controller._get_flattened_applications()
        center_panel = Div("Select an application to view details.", cls="p-4 text-center text-gray-500")
        right_panel = Div(cls="p-4")
        selected_qual_id = None

        if applications_data:
            selected_qual_id = applications_data[0].get('qual_id')
            try:
                # Unpack all 3 panels
                center_panel, right_panel, right_panel_drawer = self.show_v2_application_detail(request, selected_qual_id)
            except Exception as e:
                error(f"Error pre-loading application detail: {e}")
                traceback.print_exc()
                center_panel = Div("Error loading application.", cls="p-4 text-red-500")

        left_panel_desktop = render_left_panel(applications_data, active_qual_id=selected_qual_id)
        
        # Drawer Left: Application List (Light / Darker Dark)
        left_panel_drawer = render_left_panel(
            applications_data, 
            id_suffix="-drawer", 
            active_qual_id=selected_qual_id,
            bg_class="bg-white dark:bg-gray-950" 
        )

        return ev_layout(
            request=request, title="Hindamiskeskkond v2",
            left_panel_content=left_panel_desktop,
            center_panel_content=center_panel,
            right_panel_content=None,
            drawer_left_panel_content=left_panel_drawer,
            drawer_right_panel_content=None,
            db=self.db
        )

    def show_v2_application_detail(self, request: Request, qual_id: str):
        try:
            # Use fixed separator
            user_email, level, activity = qual_id.split(':::', 2)

            # 1. Prefer saved evaluation state for persistence
            best_state = None
            loaded_from_db = False
            try:
                # Use raw SQL for retrieval
                rows = list(self.db.execute("SELECT evaluation_state_json FROM evaluations WHERE qual_id = ?", (qual_id,)))
                if rows:
                    evaluation_state_json = rows[0][0] # First row, first column
                    saved_state_data = json.loads(evaluation_state_json)
                    debug(f"Loaded Saved State for {qual_id}: decision='{saved_state_data.get('final_decision')}'")
                    
                    best_state = self.validation_engine.dict_to_state(saved_state_data)
                    loaded_from_db = True
            except Exception as e:
                debug(f"Failed to rehydrate saved state: {e} ({type(e).__name__})")

            user_data = self.users_table[user_email]
            user_quals = [q for q in self.qual_table() if q.get('user_email') == user_email and q.get('level') == level and q.get('qualification_name') == activity]

            # 2. If no saved state, run fresh validation (pre-check)
            if best_state is None:
                qualification_rule_id = QUALIFICATION_LEVEL_TO_RULE_ID.get(level, "toojuht_tase_5")
                applicant_data = self._get_applicant_data_for_validation(user_email)
                all_states = self.validation_engine.validate(applicant_data, qualification_rule_id)
                best_state = next((s for s in all_states if s.overall_met), all_states[0])
                
                # Hydrate decision from legacy table if available
                if user_quals and user_quals[0].get('eval_decision'):
                    best_state.final_decision = user_quals[0].get('eval_decision')
                    if user_quals[0].get('eval_comment'):
                        best_state.otsus_comment = user_quals[0].get('eval_comment')
                    debug(f"Hydrated decision '{best_state.final_decision}' from applied_qualifications")
            
            qual_data = {
                "level": level, "qualification_name": activity, 
                "specialisations": [q.get('specialisation') for q in user_quals],
                "selected_specialisations_count": len(user_quals),
                "total_specialisations": len(kt.get(level, {}).get(activity, [])),
                "qual_id": qual_id
            }

            user_documents = [doc for doc in self.db.t.documents() if doc.get('user_email') == user_email]
            user_work_experience = [
                exp for exp in self.work_exp_table() 
                if exp.get('user_email') == user_email and exp.get('associated_activity') == activity
            ]

            # FORCE FORMATTING ON INITIAL LOAD
            # We want "Nõutav: X | Esitatud: Y | Vastavaks tunnistatud: 0a 0k" 
            # even if fresh validation just gave us "3.0a".
            from logic.helpers import construct_workex_header
            
            # Start with 0 accepted if fresh (or whatever saved logic might imply, but usually saved has it formatted)
            # If loaded from DB, the string might already be formatted. construct_workex_header is idempotent-ish 
            # (parses numbers out).
            
            # Recalculate accepted years just to be 100% sure sync matches DB?
            # Or just rely on 0.0 if not yet calculated.
            # If loaded_from_db is True, 'best_state' has the saved string.
            # But the accepted_ids might be present.
            
            accepted_years = 0.0
            if hasattr(best_state, 'accepted_work_experience_ids') and best_state.accepted_work_experience_ids:
                 # Minimal recalc for consistency
                 from controllers.evaluator_workbench_controller import _calculate_years
                 for exp in user_work_experience:
                     if exp.get('id') in best_state.accepted_work_experience_ids:
                         accepted_years += _calculate_years(exp.get('start_date'), exp.get('end_date'))
            
            if best_state.matching_experience.is_relevant:
                 new_header = construct_workex_header(
                    best_state.matching_experience.required,
                    best_state.matching_experience.provided, # Raw from validator or Previous saved string
                    accepted_years
                 )
                 best_state.matching_experience.provided = new_header
            
            # Also format total experience if needed (simpler format)
            if best_state.total_experience.provided:
                from logic.helpers import format_duration_est
                # Parse raw first
                try: 
                     m = re.search(r'([\d\.]+)', best_state.total_experience.provided)
                     if m: 
                         val = float(m.group(1))
                         best_state.total_experience.provided = format_duration_est(val)
                except: pass

            center_panel = render_center_panel(qual_data, user_data, best_state, user_work_experience, user_documents)
            
            # Log the final state being presented
            self._log_application_state(qual_id, best_state, source="Saved Evaluation" if loaded_from_db else "Fresh Validation")

            return center_panel, None, None

        except Exception as e:
            traceback.print_exc()
            return (
                Div(f"Error: {e}", id="ev-center-panel", hx_swap_oob="true"), 
                None,
                None
            )

    def _get_applicant_data_for_validation(self, user_email: str) -> ApplicantData:
        # 1. Fetch Education from DB
        user_education = self.db.t.education("user_email=?", [user_email])
        best_edu = "any"
        if user_education:
            from logic.validator import EDUCATION_HIERARCHY
            sorted_edu = sorted(user_education, key=lambda x: EDUCATION_HIERARCHY.get(x.get('education_category', 'any'), 0), reverse=True)
            best_edu = sorted_edu[0].get('education_category', 'any')

        # 2. Fetch Work Experience
        # work_experiences = self.work_exp_table("user_email=?", [user_email]) # potential ambiguity
        work_experiences = list(self.work_exp_table.rows_where("user_email=?", [user_email]))
        
        total_years = calculate_total_experience_years([
            (datetime.datetime.strptime(exp['start_date'], '%Y-%m').date(),
             datetime.datetime.strptime(exp['end_date'] or datetime.date.today().strftime('%Y-%m'), '%Y-%m').date())
            for exp in work_experiences if exp.get('start_date')
        ])
        
        return ApplicantData(
            education=best_edu,
            work_experience_years=total_years,
            matching_experience_years=total_years,
            has_prior_level_4=True, base_training_hours=40, manager_training_hours=30,
            cpd_training_hours=16, is_education_old_or_foreign=False
        )

    def _log_application_state(self, qual_id: str, state: ComplianceDashboardState, source: str):
        """
        Logs a detailed snapshot of the application state when loaded.
        """
        debug(f"\n--- [LOAD] Application Loaded: {qual_id} ---")
        debug(f"    Source: {source}")
        debug(f"    Overall Met: {'YES' if state.overall_met else 'NO'} (Package: {state.package_id})")
        debug(f"    Current Decision: {state.final_decision or 'None'}")
        
        # Log active comments
        comments = []
        if state.haridus_comment: comments.append(f"Haridus: '{state.haridus_comment}'")
        if state.tookogemus_comment: comments.append(f"Tookogemus: '{state.tookogemus_comment}'")
        if state.koolitus_comment: comments.append(f"Koolitus: '{state.koolitus_comment}'")
        if state.otsus_comment: comments.append(f"Otsus: '{state.otsus_comment}'")
        
        if comments:
            debug(f"    Active Comments: {'; '.join(comments)}")
        else:
            debug(f"    Active Comments: None")
            
        debug(f"----------------------------------------------\n")
