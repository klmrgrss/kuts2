# app/controllers/evaluator.py
from fasthtml.common import *
from starlette.requests import Request
from fastlite import NotFoundError
import datetime
import json
import traceback
from logic.helpers import calculate_total_experience_years
from logic.models import ApplicantData
from ui.evaluator_v2.ev_layout import ev_layout
from ui.evaluator_v2.left_panel import render_left_panel
from ui.evaluator_v2.center_panel import render_center_panel
from ui.evaluator_v2.right_panel import render_right_panel
from config.qualification_data import kt

QUALIFICATION_LEVEL_TO_RULE_ID = {
    "Ehituse tööjuht, TASE 5": "toojuht_tase_5",
    "Ehitusjuht, TASE 6": "ehitusjuht_tase_6",
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

        if applications_data:
            selected_qual_id = applications_data[0].get('qual_id')
            try:
                center_panel, right_panel = self.show_v2_application_detail(request, selected_qual_id)
            except Exception as e:
                print(f"--- ERROR pre-loading application detail: {e} ---")
                traceback.print_exc()
                center_panel = Div("Error loading application.", cls="p-4 text-red-500")

        left_panel_desktop = render_left_panel(applications_data)
        left_panel_drawer = render_left_panel(applications_data, id_suffix="-drawer")

        return ev_layout(
            request=request, title="Hindamiskeskkond v2",
            left_panel_content=left_panel_desktop,
            center_panel_content=center_panel,
            right_panel_content=right_panel,
            drawer_left_panel_content=left_panel_drawer,
            db=self.db
        )

    def show_v2_application_detail(self, request: Request, qual_id: str):
        try:
            user_email, level, activity = qual_id.split('-', 2)

            try:
                saved_evaluation = self.evaluations_table.get(qual_id)
                saved_state_data = json.loads(saved_evaluation['evaluation_state_json'])
                best_state = self.validation_engine.dict_to_state(saved_state_data)
                print(f"--- [DEBUG] Loaded saved evaluation state for {qual_id}")
            except (NotFoundError, json.JSONDecodeError):
                print(f"--- [DEBUG] No valid saved state for {qual_id}. Running initial validation.")
                qualification_rule_id = QUALIFICATION_LEVEL_TO_RULE_ID.get(level, "toojuht_tase_5")
                applicant_data = self._get_applicant_data_for_validation(user_email)
                all_states = self.validation_engine.validate(applicant_data, qualification_rule_id)
                best_state = next((s for s in all_states if s.overall_met), all_states[0])
                self.workbench_controller._save_evaluation_state(qual_id, request.session.get("user_email"), best_state)

            user_data = self.users_table[user_email]
            user_quals = [q for q in self.qual_table() if q.get('user_email') == user_email and q.get('level') == level and q.get('qualification_name') == activity]
            
            qual_data = {
                "level": level, "qualification_name": activity, 
                "specialisations": [q.get('specialisation') for q in user_quals],
                "selected_specialisations_count": len(user_quals),
                "total_specialisations": len(kt.get(level, {}).get(activity, [])),
                "qual_id": qual_id
            }

            user_documents = [doc for doc in self.db.t.documents() if doc.get('user_email') == user_email]
            user_work_experience = [exp for exp in self.work_exp_table() if exp.get('user_email') == user_email]

            center_panel = render_center_panel(qual_data, user_data, best_state)
            right_panel = render_right_panel(user_documents, user_work_experience)

            return center_panel, right_panel

        except Exception as e:
            traceback.print_exc()
            return Div(f"Error: {e}", id="ev-center-panel", hx_swap_oob="true"), Div(id="ev-right-panel", hx_swap_oob="true")

    def _get_applicant_data_for_validation(self, user_email: str) -> ApplicantData:
        work_experiences = self.work_exp_table("user_email=?", [user_email])
        total_years = calculate_total_experience_years([
            (datetime.datetime.strptime(exp['start_date'], '%Y-%m').date(),
             datetime.datetime.strptime(exp['end_date'] or datetime.date.today().strftime('%Y-%m'), '%Y-%m').date())
            for exp in work_experiences if exp.get('start_date')
        ])
        
        return ApplicantData(
            education="any",
            work_experience_years=total_years,
            matching_experience_years=total_years,
            has_prior_level_4=True, base_training_hours=40, manager_training_hours=30,
            cpd_training_hours=16, is_education_old_or_foreign=False
        )