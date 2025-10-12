# app/controllers/auth.py

from fasthtml.common import *
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from fastlite import NotFoundError
from monsterui.all import *
from auth.roles import APPLICANT, normalize_role
import traceback
from typing import Any, Dict, Optional
# Add necessary imports for certificate parsing
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from base64 import b64decode

class AuthController:
    """ Handles user authentication (login, registration, logout). """
    
    def __init__(self, db):
        self.db = db
        self.users = db.t.users
    
    def get_login_form(self, error_message: Optional[str] = None) -> FT:
        """
        Returns the new Smart-ID login form, optionally with an error message.
        """
        error_display = P(error_message, cls="text-red-500 text-center mb-4") if error_message else ""

        return Div(
            Form(
                H2("Logi sisse Smart-ID'ga"),
                P("Palun sisesta oma isikukood:", cls="text-sm text-muted-foreground"),
                error_display,
                LabelInput(
                    label="Isikukood",
                    id="national_id",
                    name="national_id",
                    placeholder="40404040009", # See docs/smart_id_testing.md for more demo IDs
                    required=True,
                ),
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
        """ DEPRECATED: This method is no longer used. """
        return Span("Password login is no longer supported.")

    @staticmethod
    def _parse_subject_fields(status_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Tries to parse the X.509 certificate; if that fails, falls back to
        parsing string-based subject fields from the Smart-ID response.
        """
        # --- Attempt 1: Parse the full X.509 certificate (most reliable) ---
        try:
            result = status_data.get("result", {})
            cert_info = result.get("cert", {})
            cert_value_b64 = cert_info.get("value")

            if cert_value_b64:
                cert_bytes = b64decode(cert_value_b64)
                certificate = x509.load_der_x509_certificate(cert_bytes, default_backend())
                
                subject_fields = {}
                for attribute in certificate.subject:
                    oid, value = attribute.oid, attribute.value
                    if oid == x509.NameOID.GIVEN_NAME: subject_fields['GIVENNAME'] = value
                    elif oid == x509.NameOID.SURNAME: subject_fields['SURNAME'] = value
                    elif oid == x509.NameOID.SERIAL_NUMBER: subject_fields['SERIALNUMBER'] = value

                if subject_fields.get("SERIALNUMBER"):
                    print(f"--- DEBUG: Successfully parsed certificate via X.509: {subject_fields} ---")
                    return subject_fields
        except Exception as e:
            print(f"--- WARNING: Failed to parse X.509 certificate ({e}). Will fall back to string parsing. ---")

        # --- Attempt 2: Fallback to string-based parsing ---
        print("--- DEBUG: Falling back to legacy string-based subject parsing. ---")
        
        def parse_string(candidate: Any) -> Dict[str, str]:
            if not isinstance(candidate, str): return {}
            return {p.split("=")[0].strip(): p.split("=")[1].strip() for p in candidate.split(",") if "=" in p}

        result = status_data.get("result", {})
        candidates = [result.get("subject")]
        if "cert" in result:
            candidates.extend([result["cert"].get(k) for k in ("subject", "subjectName", "subjectDN")])

        aggregated = {}
        for cand in candidates:
            aggregated.update(parse_string(cand))

        # Normalize keys to match what the rest of the login function expects
        final_fields = {}
        if aggregated.get("GN"): final_fields['GIVENNAME'] = aggregated.get("GN")
        if aggregated.get("SN"): final_fields['SURNAME'] = aggregated.get("SN")
        if aggregated.get("serialNumber"): final_fields['SERIALNUMBER'] = aggregated.get("serialNumber")
        
        print(f"--- DEBUG: Parsed fields via string fallback: {final_fields} ---")
        return final_fields

    @staticmethod
    def _extract_national_id(raw_serial: Optional[str]) -> Optional[str]:
        if not raw_serial: return None
        return raw_serial.split('-')[-1]

    async def process_smart_id_login(self, request: Request, status_data: dict):
        """
        Processes a successful Smart-ID login, finds or creates a user, and sets the session.
        """
        try:
            subject_fields = self._parse_subject_fields(status_data)
            national_id = self._extract_national_id(subject_fields.get("SERIALNUMBER"))

            if not national_id:
                print(f"--- ERROR [AuthController]: National ID not found in certificate: {subject_fields} ---")
                return self.get_login_form("Sisselogimine ebaõnnestus. Proovi uuesti.")

            given_name = subject_fields.get("GIVENNAME")
            surname = subject_fields.get("SURNAME")
            full_name = f"{given_name} {surname}" if given_name and surname else f"Kasutaja {national_id}"
            email = f"{national_id}@kuts2.ee"

            print(f"--- DEBUG [AuthController]: Smart-ID success for {national_id} ({full_name}) ---")

            try:
                user_records = self.users("national_id_number = ?", [national_id])
                if not user_records: raise NotFoundError
                user_data = user_records[0]
                print(f"--- DEBUG [AuthController]: Found existing user by national ID: {user_data['email']} ---")
            except NotFoundError:
                print(f"--- DEBUG [AuthController]: User with national ID {national_id} not found. Creating new user. ---")
                new_user = {"email": email, "hashed_password": "", "full_name": full_name, "birthday": None, "role": APPLICANT, "national_id_number": national_id}
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
            return self.get_login_form("Sisselogimisel tekkis ootamatu viga.")

    async def process_registration(self, request: Request, email: str, password: str, confirm_password: str, full_name: str, birthday: str):
        """ DEPRECATED: This method is no longer used. """
        return Span("Registration is now automatic via Smart-ID.")

    def logout(self, request: Request):
        """ Clears the session and redirects to the login page. """
        print(f"Logging out user: {request.session.get('user_email')}")
        request.session.clear()
        return RedirectResponse('/login', status_code=303)