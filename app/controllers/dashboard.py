# app/controllers/dashboard.py
from fasthtml.common import *
from starlette.requests import Request
from starlette.responses import RedirectResponse
from auth.roles import is_admin, is_evaluator, normalize_role
from ui.layouts import dashboard_layout
from .applicant import ApplicantController 
from .evaluator import EvaluatorController 
from datetime import datetime
from ui.dashboard_page import render_applicant_dashboard, render_evaluator_dashboard, render_admin_dashboard

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

        if is_admin(user_role):
            # Admin Dashboard
            allowed_evals = self.db.t.allowed_evaluators()
            # Convert to list of dicts if needed, or pass result set
            content = render_admin_dashboard(list(allowed_evals))
            title = "Administraatori Töölaud"

        elif is_evaluator(user_role):
            # Pure Evaluator -> Redirect to Evaluator Dashboard V2
            return RedirectResponse("/evaluator/d", status_code=303)

        else: # Default to applicant view
            # For applicants, fetch their application status
            applicant_data, applicant_name = self.applicant_controller._get_applicant_data(user_email)
            content = render_applicant_dashboard(applicant_data, applicant_name)
            title = "Minu Töölaud"

        request.session['visited_dashboard'] = True
        
        return dashboard_layout(request=request, title=title, content=content, db=self.db)
    
    async def add_evaluator(self, req: Request):
        form = await req.form()
        id_code = form.get("national_id_number")
        if id_code:
            try:
                self.db.t.allowed_evaluators.insert({
                    "national_id_number": id_code,
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "added_by": req.state.current_user.get("email")
                })
                # Check if this user exists and promote them immediately if not admin
                try:
                    user_records = self.db.t.users("national_id_number = ?", [id_code])
                    if user_records:
                        u = user_records[0]
                        if normalize_role(u['role']) != ADMIN:
                            u['role'] = EVALUATOR
                            self.db.t.users.update(u)
                except Exception as e:
                    print(f"Error promoting existing user: {e}")

            except Exception as e:
                print(f"Error adding evaluator: {e}")
        
        return self.show_dashboard(req)

    def delete_evaluator(self, req: Request, id_code: str):
        try:
            self.db.t.allowed_evaluators.delete(id_code)
            # Check if this user exists and demote them immediately if not admin
            try:
                user_records = self.db.t.users("national_id_number = ?", [id_code])
                if user_records:
                    u = user_records[0]
                    if normalize_role(u['role']) == EVALUATOR: # Only demote if they are just Evaluator
                        u['role'] = APPLICANT
                        self.db.t.users.update(u)
            except Exception as e:
                print(f"Error demoting existing user: {e}")

        except Exception as e:
            print(f"Error deleting evaluator: {e}")
            
        return self.show_dashboard(req)