# app/controllers/dashboard.py
from fasthtml.common import *
from starlette.requests import Request
from starlette.responses import RedirectResponse
from auth.roles import is_admin, is_evaluator, normalize_role
from ui.layouts import dashboard_layout
from .applicant import ApplicantController 
from .evaluator import EvaluatorController 
from ui.dashboard_page import render_applicant_dashboard, render_evaluator_dashboard

class DashboardController:
    def __init__(self, db, applicant_controller: ApplicantController, evaluator_controller: EvaluatorController):
        self.db = db
        # --- THE FIX: Receive controllers instead of creating them ---
        self.applicant_controller = applicant_controller
        self.evaluator_controller = evaluator_controller

    def show_dashboard(self, request: Request, current_user: dict | None = None):
        """
        Shows a role-specific dashboard to the user.
        This is the main landing page after login.
        """
        current_user = current_user or getattr(request.state, "current_user", {})
        user_email = current_user.get("email")
        if not user_email:
            return RedirectResponse("/login", status_code=303)

        user_role = normalize_role(current_user.get("role"))

        if is_evaluator(user_role):
            # For evaluators, fetch summary data using the search controller
            evaluator_apps = self.evaluator_controller.search_controller._get_flattened_applications()
            evaluator_data = {"applications_to_review": len(evaluator_apps)}
            content = render_evaluator_dashboard(evaluator_data)
            title = "Hindaja Töölaud" if not is_admin(user_role) else "Administraatori Töölaud"

        else: # Default to applicant view
            # For applicants, fetch their application status
            applicant_data, applicant_name = self.applicant_controller._get_applicant_data(user_email)
            content = render_applicant_dashboard(applicant_data, applicant_name)
            title = "Minu Töölaud"

        request.session['visited_dashboard'] = True
        
        return dashboard_layout(request=request, title=title, content=content, db=self.db)