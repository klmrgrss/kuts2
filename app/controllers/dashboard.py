# app/controllers/dashboard.py
from fasthtml.common import *
from starlette.requests import Request
from starlette.responses import RedirectResponse
from ui.layouts import dashboard_layout
from .applicant import ApplicantController # Re-use the data fetching logic
from .evaluator import EvaluatorController # Re-use the data fetching logic
from ui.dashboard_page import render_applicant_dashboard, render_evaluator_dashboard

class DashboardController:
    def __init__(self, db):
        self.db = db
        # Instantiate other controllers to use their helper methods
        self.applicant_controller = ApplicantController(db)
        self.evaluator_controller = EvaluatorController(db)

    def show_dashboard(self, request: Request):
        """
        Shows a role-specific dashboard to the user.
        This is the main landing page after login.
        """
        user_email = request.session.get("user_email")
        if not user_email:
            return RedirectResponse("/login", status_code=303)

        user_role = request.session.get("role")

        if user_role == 'evaluator':
            # For evaluators, fetch summary data
            evaluator_apps = self.evaluator_controller._get_flattened_applications()
            evaluator_data = {"applications_to_review": len(evaluator_apps)}
            content = render_evaluator_dashboard(evaluator_data)
            title = "Hindaja Töölaud"
        
        else: # Default to applicant view
            # For applicants, fetch their application status
            applicant_data, applicant_name = self.applicant_controller._get_applicant_data(user_email)
            content = render_applicant_dashboard(applicant_data, applicant_name)
            title = "Minu Töölaud"

        # --- THE FIX: Set a flag in the session ---
        # This confirms the user has successfully reached their designated entry point.
        request.session['visited_dashboard'] = True
        
        return dashboard_layout(request=request, title=title, content=content, db=self.db)