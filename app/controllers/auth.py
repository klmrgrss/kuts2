# app/controllers/auth.py

# Ensure necessary imports are present
import os
from fasthtml.common import *
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from fastlite import NotFoundError
from monsterui.all import *
from auth.roles import APPLICANT, EVALUATOR, ADMIN, normalize_role
from auth.utils import get_password_hash, verify_password
import traceback
from typing import Any, Dict, Optional
import hashlib, base64
from services import smart_id_service
from auth.utils import calculate_verification_code
from utils.log import log, debug, error

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
                    placeholder="40404040009", # See docs/smart_id_testing.md for more demo IDs
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

    async def initiate_smart_id(self, national_id: str) -> FT:
        if not national_id: return self.get_login_form("Isikukood on vajalik.")
        
        digest = hashlib.sha256(os.urandom(32)).digest()
        encoded = base64.b64encode(digest).decode('utf-8')
        
        sess = await smart_id_service.initiate_authentication(national_id, encoded)
        if not sess or "sessionID" not in sess: return self.get_login_form("Sessiooni alustamine ebaõnnestus.")
        
        code = calculate_verification_code(digest)
        return Div(
            H3(f"Kontrollkood: {code}", cls="text-center font-bold text-2xl tracking-wider"),
            P("Sisesta PIN1 oma Smart-ID rakenduses.", cls="text-center"),
            Div(cls="loading loading-lg mx-auto block"),
            hx_get=f"/auth/smart-id/status/{sess['sessionID']}",
            hx_trigger="load delay:3s", hx_swap="innerHTML",
            id="smart-id-login-flow", cls="space-y-4"
        )

    async def check_smart_id_status(self, req: Request, session_id: str) -> FT:
        status = await smart_id_service.check_session_status(session_id)
        if not status: 
            return Div(
                P("Kontroll ebaõnnestus.", cls="text-red-500 text-center"), 
                A(Button("Proovi uuesti"), href="/", cls="btn btn-secondary w-full"), 
                id="smart-id-login-flow", cls="space-y-4"
            )
        
        state = status.get("state")
        if state == "RUNNING":
            return Div(
                H3("Kontrollkood: ...", cls="text-center font-bold text-2xl tracking-wider"),
                P("Ootan PIN1...", cls="text-center"),
                Div(cls="loading loading-lg mx-auto block"),
                hx_get=f"/auth/smart-id/status/{session_id}",
                hx_trigger="load delay:3s", hx_swap="innerHTML",
                id="smart-id-login-flow", cls="space-y-4"
            )
        elif state == "COMPLETE": 
            return await self.process_smart_id_login(req, status)
        else:
            return Div(
                P(f"Sisselogimine ebaõnnestus: {state}", cls="text-red-500 text-center"), 
                A(Button("Proovi uuesti"), href="/", cls="btn btn-secondary w-full"), 
                id="smart-id-login-flow", cls="space-y-4 text-center"
            )

    @staticmethod
    def _parse_subject_fields(status_data: Dict[str, Any]) -> Dict[str, str]:
        """Extract subject fields from Smart-ID status response in a robust way."""
        cert_data = status_data.get("cert", {})
        cert_value = cert_data.get("value")
        if not cert_value:
            print("--- DEBUG: Certificate value not found in response. ---")
            return {}

        parsed: Dict[str, str] = {}
        result = status_data.get("result", {})
        if isinstance(result, dict):
            doc_num = result.get("documentNumber")
            if doc_num:
                parsed["serialNumber"] = doc_num

        print(f"--- DEBUG: Parsed fields from response: {parsed} ---")
        return parsed


    @staticmethod
    def _normalise_subject_field(fields: Dict[str, str], *names: str) -> Optional[str]:
        lowered = {key.lower(): value for key, value in fields.items()}
        for name in names:
            key = name.lower()
            if key in lowered and lowered[key]:
                return lowered[key]
        return None

    @staticmethod
    def _extract_national_id(raw_serial: Optional[str]) -> Optional[str]:
        if not raw_serial:
            return None
        serial = raw_serial.strip()
        # Correctly handle "PNOEE-..." format
        if serial.startswith("PNOEE-"):
            parts = serial.split('-')
            if len(parts) > 1:
                return parts[1]
        # Fallback for other formats
        if "-" in serial:
            return serial.split("-", 1)[-1]
        return serial or None

    async def process_smart_id_login(self, request: Request, status_data: dict):
        """
        Processes a successful Smart-ID login, finds or creates a user, and sets the session.
        """
        try:
            subject_fields = self._parse_subject_fields(status_data)
            raw_serial = self._normalise_subject_field(subject_fields, "serialNumber")
            national_id = self._extract_national_id(raw_serial)

            # Fallback for names - use placeholder if not found.
            given_name = self._normalise_subject_field(subject_fields, "GN", "givenName") or "Eesnimi"
            surname = self._normalise_subject_field(subject_fields, "SN", "surname") or "Perekonnanimi"


            if not national_id:
                print(f"--- ERROR [AuthController]: National ID could not be extracted from certificate. Fields: {subject_fields} ---")
                return Div(
                    "Sisselogimisel tekkis ootamatu tehniline viga. Palun proovige hiljem uuesti.",
                    A("Proovi uuesti", href="/login", cls="btn btn-primary mt-4"),
                    id="smart-id-login-flow",
                    cls="text-center text-red-500"
                )

            full_name = f"{given_name} {surname}"
            
            
            user_domain = os.environ.get("USER_ID_DOMAIN", "id.eeel.ee")
            email = f"{national_id}@{user_domain}"


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
                "Sisselogimisel tekkis ootamatu tehniline viga. Palun proovige hiljem uuesti.",
                A("Proovi uuesti", href="/login", cls="btn btn-primary mt-4"),
                id="smart-id-login-flow",
                cls="text-center text-red-500"
            )

    def logout(self, request: Request):
        """ Clears the session and redirects to the landing page. """
        print(f"Logging out user: {request.session.get('user_email')}")
        request.session.clear()
        return RedirectResponse('/', status_code=303)