# app/controllers/evaluator.py
# klmrgrss/kuts2/kuts2-eval/app/controllers/evaluator.py

from fasthtml.common import *
from monsterui.all import *
from starlette.requests import Request
from starlette.responses import JSONResponse
from fastlite import NotFoundError
from ui.layouts import evaluator_layout
import datetime
import json
import traceback
from dateutil.relativedelta import relativedelta
from collections import defaultdict
from config.qualification_data import kt

# Import the UI components used
# V2 UI Imports
from ui.evaluator_v2.ev_layout import ev_layout
from ui.evaluator_v2.left_panel import render_left_panel
from ui.evaluator_v2.center_panel import render_center_panel, render_compliance_dashboard
from ui.evaluator_v2.right_panel import render_right_panel
from ui.evaluator_v2.application_list import render_application_list
from ui.evaluator_v2.test_search_page import render_test_search_page
from logic.validator import ValidationEngine
from logic.models import ApplicantData, ComplianceDashboardState
from logic.helpers import calculate_total_experience_years

# --- Mappings and Allowed Fields (Keep as is) ---
tegevusalad_abbr_to_full = {
    "ÜE/EH": "üldehituslik ehitamine", "Põrandakatja, tase 4": "põrandakatja, tase 4",
    "KÜTE/EH": "küttesüsteemide ehitamine", "VENT/EH": "ventilatsioonisüsteemide ehitamine",
    "VK/EH": "hoonesisese ja selle juurde kuuluva vee- ja kanalisatsioonisüsteemi ehitamine",
    "SKT/EH": "sisekliima tagamise süsteemide ehitamine", "ÜVK/EH": "ühisveevärgi või kanalisatsiooni ehitamine",
    "JAHUTUS/EH": "jahutussüsteemide ehitamine", "Ventilatsioonilukksepp": "ventilatsioonilukksepp",
    "ÜE/OJV": "üldehitusliku ehitamise omanikujärelevalve tegemine",
    "SKT/OJV": "sisekliima tagamise süsteemide ehitamise omanikujärelevalve tegemine",
    "VK/OJV": "hoonesisese ja selle juurde kuuluva veevarustus- ja kanalisatsioonisüsteemi ehitamise omanikujärelevalve tegemine",
    "Maaler": "maaler", "ÜE/EHTT": "üldehitustööde tegemine",
    "Kaldkatuste/EH": "eriehitustööde tegemine, kaldkatuste ehitamine",
    "Lamekatus/EH": "eriehitustööde tegemine, lamekatuste ehitamine",
    "EH-viimistlus": "ehitusviimistlustööde tegemine", "Viimistlus": "ehitusviimistlustööde tegemine",
    "VK lukksepp": "veevärgilukksepp, tase 4", "Teras/EH": "terassüsteemide ehitamine",
    "Betoon/EH": "betoonkonstruktsioonide ehitamine", "Lammutus/EH": "lammutustööde tegemine",
    "Eriehitus": "eriehitustööde tegemine"
}
kutsetase_abbr_to_full = {
    "EJ6": "Ehitusjuht, tase 6", "ETJ5": "Ehituse tööjuht, tase 5",
    "EJT5": "Ehituse tööjuht, tase 5", "OT4": "Oskustööline, tase 4",
}
FULL_NAME_TO_ABBR_TEGEVUS = {v.lower(): k for k, v in tegevusalad_abbr_to_full.items()}
FULL_NAME_TO_ABBR_KUTSE = {v.lower(): k for k, v in kutsetase_abbr_to_full.items()}
ALLOWED_UPDATE_FIELDS = [
    'eval_education_status', 'eval_training_status', 'eval_experience_status',
    'eval_comment', 'eval_decision'
]

QUALIFICATION_LEVEL_TO_RULE_ID = {
    "Ehituse tööjuht, TASE 5": "toojuht_tase_5",
    "Ehitusjuht, TASE 6": "ehitusjuht_tase_6",
}


class EvaluatorController:
    def __init__(self, db):
        self.db = db
        self.users_table = db.t.users
        self.qual_table = db.t.applied_qualifications
        self.profile_table = db.t.applicant_profile
        self.work_exp_table = db.t.work_experience
        self.education_table = db.t.education
        self.training_files_table = db.t.training_files
        self.emp_proof_table = db.t.employment_proof
        rules_path = Path(__file__).parent.parent / 'config' / 'rules.toml'
        self.validation_engine = ValidationEngine(rules_path)

    async def re_evaluate_application(self, request: Request, qual_id: str):
        print("\n--- [DEBUG] ENTERING RE-EVALUATION ENDPOINT ---")
        try:
            user_email, level, activity = qual_id.split('-', 2)
            form_data = await request.form()
            
            print(f"--- [DEBUG] Raw form data received: {form_data}")

            selected_education = form_data.get("education_level") or "any"
            is_old_or_foreign = form_data.get("education_old_or_foreign") == "on"
            
            print(f"--- [DEBUG] Evaluator selected education: '{selected_education}', Old/Foreign: {is_old_or_foreign}")

            applicant_data_for_validation = self._get_applicant_data_for_validation(user_email)
            applicant_data_for_validation.education = selected_education
            applicant_data_for_validation.is_education_old_or_foreign = is_old_or_foreign
            
            print(f"--- [DEBUG] ApplicantData object for validation: {applicant_data_for_validation}")

            qualification_rule_id = QUALIFICATION_LEVEL_TO_RULE_ID.get(level, "toojuht_tase_5")
            print(f"--- [DEBUG] Using rule ID: '{qualification_rule_id}' for level '{level}'")
            
            all_states = self.validation_engine.validate(applicant_data_for_validation, qualification_rule_id)
            
            best_state = next((s for s in all_states if s.overall_met), all_states[0])
            print(f"--- [DEBUG] Best validation state found: Package ID '{best_state.package_id}', Overall Met: {best_state.overall_met}")

            response_html = render_compliance_dashboard(best_state)
            print("--- [DEBUG] SUCCESSFULLY RENDERED COMPLIANCE DASHBOARD HTML TO BE SENT TO CLIENT ---")
            return response_html

        except Exception as e:
            print(f"--- [ERROR] An error occurred during re-evaluation: {e} ---")
            traceback.print_exc()
            return Div(f"An error occurred during re-evaluation: {e}", cls="p-4 text-red-500")

    def _get_dashboard_data(self):
        users = self.users_table()
        all_quals = self.qual_table()
        dashboard_data = []
        for user in users:
            user_email = user.get('email')
            user_quals = [q for q in all_quals if q.get('user_email') == user_email]
            qual_summary = "; ".join(f"{q.get('level', '')} - {q.get('qualification_name', '')}" for q in user_quals[:2])
            if len(user_quals) > 2: qual_summary += "; ..."
            
            full_name = user.get('full_name')
            if not full_name:
                try:
                    profile = self.profile_table[user_email]
                    full_name = profile.get('full_name', 'N/A')
                except NotFoundError:
                    full_name = 'N/A'

            dashboard_data.append({
                "email": user.get('email'),
                "submission_date": user.get('submission_timestamp', datetime.date.today().strftime('%Y-%m-%d')),
                "full_name": full_name,
                "qualifications_summary": qual_summary if qual_summary else "None"
            })
        return dashboard_data

    def _get_flattened_applications(self):
        all_users = self.users_table()
        all_quals = self.qual_table()
        user_name_lookup = {user.get('email'): user.get('full_name', 'N/A') for user in all_users}

        grouped_by_activity = defaultdict(lambda: defaultdict(list))
        for qual in all_quals:
            user_email = qual.get('user_email')
            level = qual.get('level')
            activity = qual.get('qualification_name')
            specialisation = qual.get('specialisation')
            grouped_by_activity[user_email][(level, activity)].append(specialisation)

        flattened_data = []
        for user_email, activities in grouped_by_activity.items():
            for (level, activity), specialisations in activities.items():
                applicant_name = user_name_lookup.get(user_email, user_email)
                total_specialisations = len(kt.get(level, {}).get(activity, []))

                flattened_data.append({
                    "qual_id": f"{user_email}-{level}-{activity}",
                    "applicant_name": applicant_name,
                    "qualification_name": activity,
                    "level": level,
                    "submission_date": datetime.date.today().strftime('%Y-%m-%d'),
                    "selected_specialisations_count": len(specialisations),
                    "total_specialisations": total_specialisations,
                    "specialisations": specialisations
                })
        return flattened_data

    def show_dashboard(self, request: Request):
        page_title = "Ehitamise valdkonna kutsetaotluste HINDAMISKESKKOND"
        table_data = self._get_dashboard_data()
        table_data_json = json.dumps(table_data)
        ag_grid_dashboard_container = Div(id="ag-grid-dashboard", cls="ag-theme-quartz", style="height: 600px; width: 100%;", data_applications=table_data_json)
        ag_grid_dashboard_script = Script(src="/static/js/ag_grid_dashboard.js", defer=True)
        content = Div(ag_grid_dashboard_container, ag_grid_dashboard_script, cls="p-4")
        return evaluator_layout(request=request, title=page_title, content=content, db=self.db)

    def show_dashboard_v2(self, request: Request):
        applications_data = self._get_flattened_applications()
        center_panel = Div("Select an application to view details.", cls="p-4 text-center text-gray-500")
        right_panel = Div(cls="p-4")

        if applications_data:
            selected_qual_id = applications_data[0].get('qual_id')
            try:
                center_panel, right_panel = self.show_v2_application_detail(request, selected_qual_id)
            except Exception as e:
                print(f"--- ERROR pre-loading application detail for qual_id {selected_qual_id}: {e} ---")
                traceback.print_exc()
                center_panel = Div(f"Error loading application {selected_qual_id}.", cls="p-4 text-red-500")

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

            qualification_rule_id = QUALIFICATION_LEVEL_TO_RULE_ID.get(level, "toojuht_tase_5")
            applicant_data_for_validation = self._get_applicant_data_for_validation(user_email)
            all_states = self.validation_engine.validate(applicant_data_for_validation, qualification_rule_id)
            
            best_state = next((s for s in all_states if s.overall_met), all_states[0])

            user_data = self.users_table[user_email]
            all_quals = self.qual_table()
            user_quals = [q for q in all_quals if q.get('user_email') == user_email and q.get('level') == level and q.get('qualification_name') == activity]

            if not user_quals:
                raise NotFoundError("No matching qualifications found.")

            specialisations = [q.get('specialisation') for q in user_quals]
            total_specialisations = len(kt.get(level, {}).get(activity, []))

            qual_data = {
                "level": level, "qualification_name": activity, "specialisations": specialisations,
                "selected_specialisations_count": len(specialisations), "total_specialisations": total_specialisations,
                "qual_id": qual_id
            }

            all_docs = self.db.t.documents(order_by='id')
            user_documents = [doc for doc in all_docs if doc.get('user_email') == user_email]
            user_work_experience = [exp for exp in self.work_exp_table(order_by='id') if exp.get('user_email') == user_email]

            center_panel = render_center_panel(qual_data, user_data, best_state)
            right_panel = render_right_panel(user_documents, user_work_experience)

            return center_panel, right_panel

        except Exception as e:
            traceback.print_exc()
            return (
                Div(f"An unexpected error occurred: {e}", id="ev-center-panel", hx_swap_oob="true"),
                Div("", id="ev-right-panel", hx_swap_oob="true")
            )

    def _get_applicant_data_for_validation(self, user_email: str) -> ApplicantData:
        work_experiences = self.work_exp_table("user_email=?", [user_email])
        periods = []
        for exp in work_experiences:
            try:
                start = datetime.datetime.strptime(exp['start_date'], '%Y-%m').date()
                end_str = exp['end_date'] or datetime.datetime.now().strftime('%Y-%m')
                end = datetime.datetime.strptime(end_str, '%Y-%m').date()
                periods.append((start, end))
            except (ValueError, TypeError):
                continue
        
        total_years = calculate_total_experience_years(periods)
        
        return ApplicantData(
            education="any", # Start with an unevaluated state
            work_experience_years=total_years,
            matching_experience_years=total_years,
            has_prior_level_4=True,
            base_training_hours=40,
            manager_training_hours=30,
            cpd_training_hours=16,
            is_education_old_or_foreign=False
        )
    
    def _prepare_timeline_data(self, work_experience_list: list) -> list:
        timeline_items = []
        today_str = datetime.date.today().strftime('%Y-%m-%d')

        for exp in work_experience_list:
            exp_id, start_date_str_ym = exp.get('id'), exp.get('start_date')
            if not exp_id or not start_date_str_ym: continue

            try:
                start_date_dt = datetime.datetime.strptime(f"{start_date_str_ym}-01", '%Y-%m-%d').date()
                start_date_final = start_date_dt.strftime('%Y-%m-%d')
            except (ValueError, TypeError):
                print(f"--- WARN [Timeline Prep]: Invalid start date format '{start_date_str_ym}' for exp ID {exp_id}. Skipping.")
                continue

            end_date_str_ym = exp.get('end_date')
            end_date_final = today_str
            if end_date_str_ym:
                try:
                    end_date_dt = datetime.datetime.strptime(f"{end_date_str_ym}-01", '%Y-%m-%d').date()
                    end_date_final = (end_date_dt + relativedelta(months=1)).strftime('%Y-%m-%d')
                except (ValueError, TypeError):
                     print(f"--- WARN [Timeline Prep]: Invalid end date format '{end_date_str_ym}' for exp ID {exp_id}. Treating as ongoing.")

            tooltip_content = (f"Roll: {exp.get('role', 'N/A')}<br>"
                             f"Objekt: {exp.get('object_address', 'N/A')}<br>"
                             f"Ettevõte: {exp.get('company_name', 'N/A')}<br>"
                             f"Periood: {start_date_str_ym} - {end_date_str_ym or 'Praeguseni'}")

            timeline_items.append({
                "id": exp_id, "group": exp_id,
                "content": exp.get('object_address', f"Töö nr {exp_id}"),
                "start": start_date_final, "end": end_date_final,
                "title": tooltip_content
            })
        return timeline_items

    def search_applications(self, request: Request, search: str):
        print(f"--- Searching applications with term: '{search}' ---")

        all_apps = self._get_flattened_applications()

        if search:
            search_lower = search.lower()
            filtered_apps = [
                app for app in all_apps if
                (search_lower in app.get('applicant_name', '').lower()) or
                (search_lower in app.get('qualification_name', '').lower()) or
                (search_lower in app.get('level', '').lower())
            ]
        else:
            filtered_apps = all_apps

        return render_application_list(filtered_apps, include_oob=False)

    def show_test_search_page(self, request: Request):
        all_apps = self._get_flattened_applications()
        return render_test_search_page(all_apps)

    def handle_test_search(self, request: Request, search: str):
        all_apps = self._get_flattened_applications()
        search_term = search.lower().strip()

        if not search_term:
            filtered_apps = all_apps
        else:
            filtered_apps = [
                app for app in all_apps if
                search_term in app.get('applicant_name', '').lower() or
                search_term in app.get('qualification_name', '').lower()
            ]

        def show_contacts(apps: list[dict]):
            if not apps:
                return Tr(Td("No matching applications found.", colspan="3", cls="text-center"))
            return [
                Tr(
                    Td(app.get('applicant_name', 'N/A')),
                    Td(app.get('qualification_name', 'N/A')),
                    Td(app.get('submission_date', 'N/A'))
                ) for app in apps
            ]

        return tuple(show_contacts(filtered_apps))