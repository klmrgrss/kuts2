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
from dateutil.relativedelta import relativedelta # For adding months to dates
from collections import defaultdict
from config.qualification_data import kt

# Import the UI components used
from ui.evaluator.references_display import render_references_grid
from ui.evaluator.applicant_summary import render_applicant_summary
from ui.evaluator.qualifications_table import render_qualifications_table
from ui.evaluator.work_exp_objects import render_work_experience_objects
from ui.evaluator.timeline_display import render_timeline_display
# V2 UI Imports
from ui.evaluator_v2.ev_layout import ev_layout
from ui.evaluator_v2.left_panel import render_left_panel
from ui.evaluator_v2.center_panel import render_center_panel
from ui.evaluator_v2.right_panel import render_right_panel
from ui.evaluator_v2.application_list import render_application_list
from ui.evaluator_v2.test_search_page import render_test_search_page
from logic.validator import ValidationEngine
from logic.models import ApplicantData
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

                # V --- INITIALIZE THE VALIDATION ENGINE --- V
        rules_path = Path(__file__).parent.parent / 'config' / 'rules.toml'
        self.validation_engine = ValidationEngine(rules_path)
        # ^ --- END INITIALIZATION --- ^

    def _get_dashboard_data(self):
        print("--- Fetching data for evaluator dashboard ---"); users = self.users_table(); all_quals = self.qual_table()
        dashboard_data = []
        for user in users:
            user_email = user.get('email'); user_quals = [q for q in all_quals if q.get('user_email') == user_email]
            qual_summary = "; ".join( f"{q.get('level', '')} - {q.get('qualification_name', '')}" for q in user_quals[:2])
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
        """
        Fetches and flattens application data, now providing 'level' and
        'qualification_name' as separate fields to match the UI component's needs.
        """
        print("--- Fetching and flattening data for V2 evaluator dashboard ---")
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
        page_title = "Ehitamise valdkonna kutsetaotluste HINDAMISKESKKOND"; table_data = self._get_dashboard_data(); table_data_json = json.dumps(table_data)
        ag_grid_dashboard_container = Div( id="ag-grid-dashboard", cls="ag-theme-quartz", style="height: 600px; width: 100%;", data_applications=table_data_json )
        ag_grid_dashboard_script = Script(src="/static/js/ag_grid_dashboard.js", defer=True)
        content = Div(ag_grid_dashboard_container, ag_grid_dashboard_script, cls="p-4")
        # --- MODIFIED: Pass db to the layout ---
        return evaluator_layout(request=request, title=page_title, content=content, db=self.db)

    # V --- MODIFIED METHOD --- V
    def show_dashboard_v2(self, request: Request):
        """Renders the new V2 dashboard layout, pre-selecting the first item."""
        applications_data = self._get_flattened_applications()
        center_panel = Div("Select an application to view details.", cls="p-4 text-center text-gray-500")
        right_panel = Div(cls="p-4")

        if applications_data:
            selected_qual_id = applications_data[0].get('qual_id')
            try:
                # Pass the qualification ID to the detail view
                center_panel, right_panel = self.show_v2_application_detail(request, selected_qual_id)
            except Exception as e:
                print(f"--- ERROR pre-loading application detail for qual_id {selected_qual_id}: {e} ---")
                traceback.print_exc()
                center_panel = Div(f"Error loading application {selected_qual_id}.", cls="p-4 text-red-500")

        left_panel = render_left_panel(applications_data)

        # --- MODIFIED: Pass db to the layout ---
        return ev_layout(
            request=request,
            title="Hindamiskeskkond v2",
            left_panel_content=left_panel,
            center_panel_content=center_panel,
            right_panel_content=right_panel,
            db=self.db
        )
    # ^ --- END MODIFIED METHOD --- ^

    def show_v2_application_detail(self, request: Request, qual_id: str):
        """
        Fetches data, runs validation, and returns the HTML partials for the center and right panels.
        """
        try:
            user_email, level, activity = qual_id.split('-', 2)
            
            # --- Run Validation ---
            applicant_data_for_validation = self._get_applicant_data_for_validation(user_email)
            validation_results = self.validation_engine.validate(applicant_data_for_validation, "toojuht_tase_5") # Using TJ5 for now

            # --- Fetch Data for UI ---
            user_data = self.users_table[user_email]
            all_quals = self.qual_table()
            user_quals = [q for q in all_quals if q.get('user_email') == user_email and q.get('level') == level and q.get('qualification_name') == activity]
            
            if not user_quals:
                raise NotFoundError("No matching qualifications found for this activity.")
                
            specialisations = [q.get('specialisation') for q in user_quals]
            total_specialisations = len(kt.get(level, {}).get(activity, []))
            
            qual_data = {
                "level": level, "qualification_name": activity, "specialisations": specialisations,
                "selected_specialisations_count": len(specialisations), "total_specialisations": total_specialisations,
            }

            all_docs = self.db.t.documents(order_by='id')
            user_documents = [doc for doc in all_docs if doc.get('user_email') == user_email]
            
            all_work_exp = self.work_exp_table(order_by='id')
            user_work_experience = [exp for exp in all_work_exp if exp.get('user_email') == user_email]

            # --- Render Panels ---
            center_panel = render_center_panel(qual_data, user_data, validation_results) # Pass results to view
            right_panel = render_right_panel(user_documents, user_work_experience)
            
            return center_panel, right_panel

        except NotFoundError:
            return (
                Div("Error: Application not found.", id="ev-center-panel", hx_swap_oob="true"),
                Div("Please select another application.", id="ev-right-panel", hx_swap_oob="true")
            )
        except Exception as e:
            traceback.print_exc()
            return (
                Div(f"An unexpected error occurred: {e}", id="ev-center-panel", hx_swap_oob="true"),
                Div("", id="ev-right-panel", hx_swap_oob="true")
            )
    # ^ --- END MODIFIED METHOD --- ^

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

    def show_application_detail(self, request: Request, user_email: str):
        current_user_email = request.session.get("user_email")
        if not current_user_email:
            return evaluator_layout(request=request, title="Error", content=Div(H2("Authentication Required"), P("Please log in as an evaluator."), cls="text-red-500 text-center p-4"))

        try:
            user_data = self.users_table[user_email]
            applicant_name = user_data.get('full_name', user_email)
            
            quals = [q for q in self.qual_table(order_by='id') if q.get('user_email') == user_email]
            for q in quals:
                q['qualification_abbr'] = FULL_NAME_TO_ABBR_TEGEVUS.get(q.get('qualification_name', '').lower(), q.get('qualification_name', ''))
                q['level_abbr'] = FULL_NAME_TO_ABBR_KUTSE.get(q.get('level', '').lower(), q.get('level', ''))
            
            work_exp = [exp for exp in self.work_exp_table(order_by='id') if exp.get('user_email') == user_email]
            edu_data = next((edu for edu in self.education_table(order_by='id') if edu.get('user_email') == user_email), {})
            training_files = [tf for tf in self.training_files_table(order_by='id') if tf.get('user_email') == user_email]
            emp_proof = self.emp_proof_table.get(user_email, {})
            
            page_title = f"Taotlus: {applicant_name} ({user_email}) | Hindamiskeskkond"
            
            summary = render_applicant_summary(user_data=user_data, education_data=edu_data, training_files=training_files, emp_proof_data=emp_proof)
            qual_table = render_qualifications_table(qualifications_data=quals, applicant_email=user_email)
            work_exp_objects = render_work_experience_objects(work_exp)
            references = render_references_grid()
            timeline_json = json.dumps(self._prepare_timeline_data(work_exp))
            timeline = render_timeline_display(timeline_json)
            
            grid = Div(Div(work_exp_objects, cls="lg:col-span-2"), Div(references, cls="lg:col-span-1"), cls="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-4 items-start")
            content = Div(summary, qual_table, grid, timeline, Hr(cls="my-6"), A("Tagasi töölauale", href="/evaluator/dashboard", cls="btn btn-secondary mt-4"))
            
            # --- MODIFIED: Pass db to the layout ---
            return evaluator_layout(request=request, title=page_title, content=content, db=self.db)

        except NotFoundError:
            return evaluator_layout(request=request, title="Not Found", content=Div(H2("Applicant Not Found"), P(f"No base user record found for user: {user_email}"), cls="text-red-500 text-center p-4"), db=self.db)
        except Exception as e:
            traceback.print_exc()
            return evaluator_layout(request=request, title="Error", content=Div(H2("Error Loading Data"), P("An unexpected error occurred."), cls="text-red-500 text-center p-4"), db=self.db)

    def search_applications(self, request: Request, search: str):
        """
        Handles the live search request. It now only filters data and delegates
        rendering to the dedicated 'render_application_list' component.
        """
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
        """Renders the simple test search page with all applications."""
        all_apps = self._get_flattened_applications()
        return render_test_search_page(all_apps)

    def handle_test_search(self, request: Request, search: str):
        """Handles the search POST request and returns only the table rows."""
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

    # V --- NEW HELPER METHOD --- V
    def _get_applicant_data_for_validation(self, user_email: str) -> ApplicantData:
        """
        Fetches real data from the DB, calculates experience, and adds placeholders
        for data that will eventually come from document parsing.
        """
        
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
        
        # --- PSEUDO-DATA SECTION ---
        pseudo_data = {
            "education": "upper_secondary",
            "has_prior_level_4": True,
            "base_training_hours": 40,
            "matching_experience_years": total_years
        }
        # --- END PSEUDO-DATA SECTION ---

        return ApplicantData(
            education=pseudo_data["education"],
            work_experience_years=total_years,
            matching_experience_years=pseudo_data["matching_experience_years"],
            has_prior_level_4=pseudo_data["has_prior_level_4"],
            base_training_hours=pseudo_data["base_training_hours"]
        )
    # ^ --- END NEW HELPER METHOD --- ^

    async def update_qualification_status(self, request: Request, user_email: str, record_id: int):
        current_user_email = request.session.get("user_email")
        if not current_user_email: return JSONResponse({'error': 'Authentication required'}, status_code=401)
        
        try:
            payload = await request.json()
            field, value = payload.get('field'), payload.get('value')
            if field not in ALLOWED_UPDATE_FIELDS:
                return JSONResponse({'error': f'Invalid field: {field}'}, status_code=400)

            record = self.qual_table[record_id]
            if record.get('user_email') != user_email:
                 return JSONResponse({'error': 'Record mismatch or access denied'}, status_code=403)

            self.qual_table.update({field: value}, id=record_id)
            return JSONResponse({'message': 'Update successful'}, status_code=200)
            
        except NotFoundError:
            return JSONResponse({'error': 'Record not found'}, status_code=404)
        except Exception as e:
            traceback.print_exc()
            return JSONResponse({'error': 'Database update failed'}, status_code=500)