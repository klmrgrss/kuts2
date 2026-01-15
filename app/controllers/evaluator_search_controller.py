# app/controllers/evaluator_search_controller.py

from fasthtml.common import *
from starlette.requests import Request
from collections import defaultdict
import json
from config.qualification_data import kt
from ui.evaluator_v2.application_list import render_application_list

class EvaluatorSearchController:
    def __init__(self, db, validation_engine):
        self.db = db
        self.validation_engine = validation_engine
        self.users_table = db.t.users
        self.qual_table = db.t.applied_qualifications

    def _get_flattened_applications(self):
        """
        Fetches and flattens application data for the search list.
        """
        all_users = self.users_table()
        all_quals = self.qual_table()
        all_evals = self.db.t.evaluations()
        user_name_lookup = {user.get('email'): user.get('full_name', 'N/A') for user in all_users}
        eval_lookup = {}
        for ev in all_evals:
            try:
                state = json.loads(ev.get('evaluation_state_json', '{}'))
                eval_lookup[ev.get('qual_id')] = {
                    "precheck_met": state.get('overall_met'),
                    "final_decision": state.get('final_decision')
                }
            except: continue

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
                if not level or not activity: continue
                applicant_name = user_name_lookup.get(user_email, user_email)
                total_specialisations = len(kt.get(level, {}).get(activity, []))

                qual_id = f"{user_email}:::{level}:::{activity}"
                eval_info = eval_lookup.get(qual_id)

                precheck_met = None
                final_decision = None

                if eval_info:
                    precheck_met = eval_info.get('precheck_met')
                    final_decision = eval_info.get('final_decision')
                
                # If no precheck met status in DB, we could optionally run a fast check here
                # but for now we rely on the saved state. If None, it shows "Pending" in UI.

                flattened_data.append({
                    "qual_id": qual_id,
                    "applicant_name": applicant_name,
                    "qualification_name": activity,
                    "level": level,
                    "submission_date": "2025-10-20", # Placeholder
                    "selected_specialisations_count": len(specialisations),
                    "total_specialisations": total_specialisations,
                    "specialisations": specialisations,
                    "precheck_met": precheck_met,
                    "final_decision": final_decision
                })
        return sorted(flattened_data, key=lambda x: x['applicant_name'])

    def get_application_by_id(self, qual_id: str):
        """Fetches data for a single application."""
        all_apps = self._get_flattened_applications()
        return next((app for app in all_apps if app['qual_id'] == qual_id), None)

    def search_applications(self, request: Request, search: str):
        """
        Handles the live search request and returns the filtered application list.
        """
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