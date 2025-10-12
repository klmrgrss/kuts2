# app/controllers/auth.py

# Ensure necessary imports are present
from fasthtml.common import *
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from fastlite import NotFoundError
from monsterui.all import *
from auth.roles import APPLICANT, normalize_role
from auth.utils import get_password_hash, verify_password
import traceback

class AuthController:
    """ Handles user authentication (login, registration, logout). """
    
    def __init__(self, db):
        self.db = db
        self.users = db.t.users
    
    def get_login_form(self) -> FT:
        """Returns the new Smart-ID login form."""
        return Div(
            Form(
                H2("Logi sisse Smart-ID'ga"),
                P("Palun sisesta oma isikukood:", cls="text-sm text-muted-foreground"),
                LabelInput(
                    label="Isikukood", 
                    id="national_id", 
                    name="national_id", 
                    placeholder="60001019906", # A known working test ID
                    required=True,
                ),
                Span(id="sid-error", cls="text-red-500"), 
                Button("Logi sisse", type="submit", cls="w-full"),
                hx_post="/auth/smart-id/initiate",
                hx_target="#smart-id-login-flow",
                hx_swap="innerHTML",
                cls="space-y-4" 
            ),
            id="smart-id-login-flow"
        )
    
    def get_register_form(self) -> FT:
        """DEPRECATED: Returns a message indicating registration is automatic."""
        return Div(
            H2("Registreerumine"),
            P("Süsteemi registreerumine toimub automaatselt esimesel sisselogimisel Smart-ID'ga."),
            A("Tagasi sisselogimise lehele", href="/login", cls="link"),
            cls="text-center space-y-4"
        )
        
    async def process_login(self, request: Request, email: str, password: str):
        """ DEPRECATED: Processes login using parameters passed from the route handler. """
        return Span("Password login is no longer supported.")

    async def process_smart_id_login(self, request: Request, status_data: dict):
        """
        Processes a successful Smart-ID login, finds or creates a user, and sets the session.
        """
        try:
            result = status_data.get("result", {})
            cert = result.get("cert", {})
            subject_cert = cert.get("subject", {})
            
            # +++ THE FINAL FIX: Use the direct fields, not the CN string +++
            given_name = subject_cert.get("GN")
            surname = subject_cert.get("SN")
            national_id = subject_cert.get("serialNumber")
            # +++ END FIX +++

            if not all([given_name, surname, national_id]):
                print(f"--- ERROR [AuthController]: Missing required fields from certificate: {subject_cert} ---")
                return Div(
                    "Sertifikaadi andmete lugemine ebaõnnestus. Palun proovi uuesti.",
                    A("Proovi uuesti", href="/login", cls="btn btn-primary mt-4"),
                    id="smart-id-login-flow",
                    cls="text-center text-red-500"
                )

            full_name = f"{given_name} {surname}"
            email = f"{national_id}@kuts2.ee"

            print(f"--- DEBUG [AuthController]: Smart-ID success for {national_id} ({full_name}) ---")

            try:
                user_records = self.users("national_id_number = ?", [national_id])
                if not user_records: raise NotFoundError
                user_data = user_records[0]
                print(f"--- DEBUG [AuthController]: Found existing user by national ID: {user_data['email']} ---")

            except NotFoundError:
                print(f"--- DEBUG [AuthController]: User with national ID {national_id} not found. Creating new user. ---")
                new_user = {
                    "email": email, "hashed_password": "", "full_name": full_name,
                    "birthday": None, "role": APPLICANT, "national_id_number": national_id
                }
                self.users.insert(new_user, pk='email')
                user_data = new_user

            request.session['authenticated'] = True
            request.session['user_email'] = user_data['email']
            request.session['role'] = normalize_role(user_data.get('role'), default=APPLICANT)
            
            print(f"--- DEBUG [AuthController]: Session created for {user_data['email']}. Redirecting to dashboard. ---")
            
            return Response(headers={'HX-Redirect': '/dashboard'})

        except Exception as e:
            print(f"--- ERROR [AuthController]: Failed to process Smart-ID login: {e} ---")
            traceback.print_exc()
            return Div(
                f"Sisselogimisel tekkis ootamatu viga: {e}",
                A("Proovi uuesti", href="/login", cls="btn btn-primary mt-4"),
                id="smart-id-login-flow",
                cls="text-center text-red-500"
            )

    async def process_registration(self, request: Request, email: str, password: str, confirm_password: str, full_name: str, birthday: str):
        """ DEPRECATED: Processes registration. """
        return Span("Registration is now automatic via Smart-ID.")

    def logout(self, request: Request):
        """ Clears the session and redirects to the login page. """
        print(f"Logging out user: {request.session.get('user_email')}")
        request.session.clear()
        return RedirectResponse('/login', status_code=303)