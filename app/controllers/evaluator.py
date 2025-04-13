# controllers/evaluator.py

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

# Import the UI components used
from ui.evaluator.references_display import render_references_grid
from ui.evaluator.applicant_summary import render_applicant_summary
from ui.evaluator.qualifications_table import render_qualifications_table
from ui.evaluator.work_exp_objects import render_work_experience_objects
# +++ ADD Import for the new timeline display component +++
from ui.evaluator.timeline_display import render_timeline_display


# --- Mappings and Allowed Fields (Keep as is) ---
tegevusalad_abbr_to_full = {
    "ÜE/EH": "üldehituslik ehitamine", "Põrandakatja, tase 4": "põrandakatja, tase 4",
    "KÜTE/EH": "küttesüsteemide ehitamine", "VENT/EH": "ventilatsioonisüsteemide ehitamine",
    "VK/EH": "hoonesisese ja selle juurde kuuluva vee- ja kanalisatsioonisüsteemi ehitamine",
    "SKT/EH": "sisekliima tagamise süsteemide ehitamine", "ÜVK/EH": "ühisveevärgi või kanalisatsiooni ehitamine",
    "JAHUTUS/EH": "jahutussüsteemide ehitamine", "Ventilatsioonilukksepp": "ventilatsioonilukksepp",
    "ÜE/OJV": "üldehitusliku ehitamise omanikujärelevalve tegemine",
    "SKT/OJV": "sisekliima tagamise süsteemide ehitamise omanikujärelevalve tegemine",
    "VK/OJV": "hoonesisese ja selle juurde kuuluva vee- ja kanalisatsioonisüsteemi ehitamise omanikujärelevalve tegemine",
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
        # --- Keep __init__ as is ---
        self.db = db
        self.users_table = db.t.users
        self.qual_table = db.t.applied_qualifications
        self.profile_table = db.t.applicant_profile
        self.work_exp_table = db.t.work_experience
        self.education_table = db.t.education
        self.training_files_table = db.t.training_files
        self.emp_proof_table = db.t.employment_proof

    def _get_dashboard_data(self):
        # --- Keep _get_dashboard_data as is ---
        print("--- Fetching data for evaluator dashboard ---"); users = self.users_table(); all_quals = self.qual_table()
        dashboard_data = []
        for user in users:
            user_email = user.get('email'); user_quals = [q for q in all_quals if q.get('user_email') == user_email]
            # Check if qual_summary should include specialisation - adjust if needed
            qual_summary = "; ".join( f"{q.get('level', '')} - {q.get('qualification_name', '')}" for q in user_quals[:2])
            if len(user_quals) > 2: qual_summary += "; ..."
            # Fetch user's full name for display
            full_name = user.get('full_name')
            if not full_name: # Fallback to profile if needed (though users table should ideally have it)
                 try:
                     profile = self.profile_table[user_email]
                     full_name = profile.get('full_name', 'N/A')
                 except NotFoundError:
                     full_name = 'N/A'

            dashboard_data.append({
                 "email": user.get('email'),
                 "submission_date": user.get('submission_timestamp', datetime.date.today().strftime('%Y-%m-%d')), # Use a real timestamp if available
                 "full_name": full_name,
                 "qualifications_summary": qual_summary if qual_summary else "None"
            })
        return dashboard_data


    def show_dashboard(self, request: Request):
        # --- Keep show_dashboard as is ---
        page_title = "Ehitamise valdkonna kutsetaotluste HINDAMISKESKKOND"; table_data = self._get_dashboard_data(); table_data_json = json.dumps(table_data)
        ag_grid_dashboard_container = Div( id="ag-grid-dashboard", cls="ag-theme-quartz", style="height: 600px; width: 100%;", data_applications=table_data_json )
        ag_grid_dashboard_script = Script(src="/static/js/ag_grid_dashboard.js", defer=True)
        content = Div(ag_grid_dashboard_container, ag_grid_dashboard_script, cls="p-4")
        return evaluator_layout(request=request, title=page_title, content=content)

    # +++ ADDED HELPER for timeline data preparation +++
    def _prepare_timeline_data(self, work_experience_list: list) -> list:
        """Transforms work experience data for Vis.js timeline."""
        timeline_items = []
        today_str = datetime.date.today().strftime('%Y-%m-%d') # Get current date as string

        for exp in work_experience_list:
            exp_id = exp.get('id')
            start_date_str_ym = exp.get('start_date') # Format: YYYY-MM

            if not exp_id or not start_date_str_ym:
                continue # Skip if no ID or start date

            # Convert YYYY-MM start date to YYYY-MM-01
            try:
                start_date_dt = datetime.datetime.strptime(f"{start_date_str_ym}-01", '%Y-%m-%d').date()
                start_date_final = start_date_dt.strftime('%Y-%m-%d')
            except (ValueError, TypeError):
                print(f"--- WARN [Timeline Prep]: Invalid start date format '{start_date_str_ym}' for exp ID {exp_id}. Skipping.")
                continue # Skip this record if start date is invalid

            # Handle end date
            end_date_str_ym = exp.get('end_date') # Format: YYYY-MM
            end_date_final = None
            if end_date_str_ym:
                try:
                    # Convert YYYY-MM end date to the *first day of the next month*
                    end_date_dt = datetime.datetime.strptime(f"{end_date_str_ym}-01", '%Y-%m-%d').date()
                    # Add one month using dateutil.relativedelta
                    next_month_start_dt = end_date_dt + relativedelta(months=1)
                    end_date_final = next_month_start_dt.strftime('%Y-%m-%d')
                except (ValueError, TypeError):
                     print(f"--- WARN [Timeline Prep]: Invalid end date format '{end_date_str_ym}' for exp ID {exp_id}. Treating as ongoing.")
                     # Fallback: Treat as ongoing (use today's date for visualization end)
                     end_date_final = today_str # Use current date for visualization if end date is invalid
            else:
                # No end date provided - treat as ongoing (end visualization today)
                end_date_final = today_str

            # Create tooltip content (adjust as needed)
            tooltip_content = f"Roll: {exp.get('role', 'N/A')}<br>"
            tooltip_content += f"Objekt: {exp.get('object_address', 'N/A')}<br>"
            tooltip_content += f"Ettevõte: {exp.get('company_name', 'N/A')}<br>"
            tooltip_content += f"Periood: {start_date_str_ym} - {end_date_str_ym or 'Praeguseni'}"

            timeline_items.append({
                "id": exp_id,
                "group": exp_id, # Each item on its own row/group
                "content": exp.get('object_address', f"Töö nr {exp_id}"), # Label on the timeline bar
                "start": start_date_final,
                "end": end_date_final,
                "title": tooltip_content # Content for the hover tooltip
            })

        print(f"--- DEBUG [Timeline Prep]: Prepared {len(timeline_items)} items for timeline. ---")
        return timeline_items
    # +++ END HELPER +++


    def show_application_detail(self, request: Request, user_email: str):
        """Renders the detailed application view including the new timeline."""
        print(f"--- Loading application detail view for: {user_email} ---")

        current_user_email = request.session.get("user_email")
        if not current_user_email:
            error_content = Div(H2("Authentication Required"), P("Please log in as an evaluator."), cls="text-red-500 text-center p-4")
            return evaluator_layout(request=request, title="Error", content=error_content)

        # Initialize data containers
        applicant_user_data = {}
        applicant_applied_quals = []
        applicant_work_exp = []
        education_data = {}
        training_files_list = []
        emp_proof_data = {}
        applicant_name = user_email

        try:
            # --- Data Fetching Logic (largely unchanged) ---
            applicant_user_data = self.users_table[user_email]
            try: applicant_profile_data = self.profile_table[user_email]
            except NotFoundError: applicant_profile_data = {}
            applicant_name = applicant_user_data.get('full_name', user_email)

            all_applied_quals = self.qual_table(order_by='id')
            applicant_applied_quals = [q for q in all_applied_quals if q.get('user_email') == user_email]
            for qual in applicant_applied_quals:
                 full_qual_name = qual.get('qualification_name', ''); full_level_name = qual.get('level', '')
                 qual['qualification_abbr'] = FULL_NAME_TO_ABBR_TEGEVUS.get(full_qual_name.lower(), full_qual_name)
                 qual['level_abbr'] = FULL_NAME_TO_ABBR_KUTSE.get(full_level_name.lower(), full_level_name)
                 qual.setdefault('eval_education_status', None); qual.setdefault('eval_training_status', None)
                 qual.setdefault('eval_experience_status', None); qual.setdefault('eval_comment', '')
                 qual.setdefault('eval_decision', None)

            all_work_exp = self.work_exp_table(order_by='id')
            applicant_work_exp = [exp for exp in all_work_exp if exp.get('user_email') == user_email]

            all_education = self.education_table(order_by='id')
            user_education_list = [edu for edu in all_education if edu.get('user_email') == user_email]
            if user_education_list: education_data = user_education_list[0]

            all_training_files = self.training_files_table(order_by='id')
            training_files_list = [tf for tf in all_training_files if tf.get('user_email') == user_email]

            try: emp_proof_data = self.emp_proof_table[user_email]
            except NotFoundError: emp_proof_data = {}

        except NotFoundError:
            error_content = Div(H2("Applicant Not Found"), P(f"No base user record found for user: {user_email}"), cls="text-red-500 text-center p-4")
            return evaluator_layout(request=request, title="Not Found", content=error_content)
        except Exception as e:
            print(f"--- ERROR fetching data for detail view: {e} ---"); traceback.print_exc()
            error_content = Div(H2("Error Loading Data"), P("An unexpected error occurred."), cls="text-red-500 text-center p-4")
            return evaluator_layout(request=request, title="Error", content=error_content)

        page_title = f"Taotlus: {applicant_name} ({user_email}) | Hindamiskeskkond"

        # --- Render Page Sections ---
        applicant_summary_section = render_applicant_summary(
            user_data=applicant_user_data, education_data=education_data,
            training_files=training_files_list, emp_proof_data=emp_proof_data
        )
        qualifications_table_section = render_qualifications_table(
            qualifications_data=applicant_applied_quals, applicant_email=user_email
        )
        work_experience_section = render_work_experience_objects(applicant_work_exp)
        references_section = render_references_grid()

        # --- Prepare and Render Timeline Section ---
        timeline_data = self._prepare_timeline_data(applicant_work_exp)
        timeline_data_json = json.dumps(timeline_data)
        timeline_section = render_timeline_display(timeline_data_json)
        # --- End Timeline Section ---


        # --- Grid container for Work Experience and References ---
        work_exp_references_grid = Div(
            Div(work_experience_section, cls="lg:col-span-2"), # Work Exp takes 2/3
            Div(references_section, cls="lg:col-span-1"),      # References takes 1/3
            cls="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-4 items-start"
        )

        # --- Assemble all page content ---
        all_page_content = Div(
            applicant_summary_section,
            qualifications_table_section,
            work_exp_references_grid,
            # +++ ADD Timeline Section Here +++
            timeline_section,
            # +++ END Timeline Section +++
            Hr(cls="my-6"), # Increased margin for separation
            A("Tagasi töölauale", href="/evaluator/dashboard", cls="btn btn-secondary mt-4")
        )

        return evaluator_layout(request=request, title=page_title, content=all_page_content)

    async def update_qualification_status(self, request: Request, user_email: str, record_id: int):
        # --- Keep update_qualification_status as is ---
        print(f"--- HANDLER REACHED: update_qualification_status for Qual ID: {record_id}, Applicant: {user_email} ---")
        current_user_email = request.session.get("user_email");
        if not current_user_email: return JSONResponse({'error': 'Authentication required'}, status_code=401)
        try: payload = await request.json(); field_to_update = payload.get('field'); new_value = payload.get('value')
        except Exception as e: print(f"--- ERROR: Invalid JSON payload: {e} ---"); return JSONResponse({'error': 'Invalid request body'}, status_code=400)
        if not field_to_update or field_to_update not in ALLOWED_UPDATE_FIELDS: print(f"--- ERROR: Invalid or disallowed field: '{field_to_update}' ---"); return JSONResponse({'error': f'Invalid field: {field_to_update}'}, status_code=400)
        try:
            record = self.qual_table[record_id];
            # Ownership/Existence check (important!)
            if record.get('user_email') != user_email:
                 print(f"--- ERROR: Attempt to update record ID {record_id} not belonging to {user_email} ---")
                 return JSONResponse({'error': 'Record mismatch or access denied'}, status_code=403) # Forbidden

            update_data = {field_to_update: new_value}
            self.qual_table.update(update_data, id=record_id)
            print(f"--- SUCCESS: Updated Qual ID {record_id}, field '{field_to_update}' ---")
            return JSONResponse({'message': 'Update successful'}, status_code=200)
        except NotFoundError: print(f"--- ERROR: Qualification record not found: {record_id} ---"); return JSONResponse({'error': 'Record not found'}, status_code=404)
        except Exception as e: print(f"--- ERROR: Database update failed for Qual ID {record_id}, field '{field_to_update}': {e} ---"); traceback.print_exc(); return JSONResponse({'error': 'Database update failed'}, status_code=500)