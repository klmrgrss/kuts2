# app/controllers/auth.py

# Ensure necessary imports are present
from fasthtml.common import *
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from fastlite import NotFoundError # Make sure NotFoundError is imported if using fastlite < 0.1.5
from monsterui.all import *
from auth.roles import APPLICANT, normalize_role
from auth.utils import get_password_hash, verify_password
import traceback # Import traceback

# Import MonsterUI components needed for forms
from monsterui.all import *

# Import password hashing utilities
from auth.utils import get_password_hash, verify_password

# Import User model for type hinting if desired (optional)
# from models import User 

class AuthController:
    """ Handles user authentication (login, registration, logout). """
    
    def __init__(self, db):
        """
        Initialize with the database connection object.
        Args:
            db: The fastlite database connection object.
        """
        self.db = db
        self.users = db.t.users # Convenience accessor for the users table
    
    def get_login_form(self) -> FT:
        """Returns the new Smart-ID login form."""
        # This is the container that will be replaced by the polling UI.
        return Div(
            Form(
                H2("Logi sisse Smart-ID'ga"),
                P("Palun sisesta oma isikukood:", cls="text-sm text-muted-foreground"),
                LabelInput(
                    label="Isikukood", 
                    id="national_id", 
                    name="national_id", 
                    placeholder="38001011234", 
                    required=True,
                    # Add pattern for basic validation if desired
                    # pattern="[0-9]{11}" 
                ),
                # Span to display errors
                Span(id="sid-error", cls="text-red-500"), 
                Button("Logi sisse", type="submit", cls="w-full"),
                
                # HTMX attributes for form submission
                hx_post="/auth/smart-id/initiate",
                hx_target="#smart-id-login-flow", # Target the outer container for replacement
                hx_swap="innerHTML",
                cls="space-y-4" 
            ),
            id="smart-id-login-flow" # The target for replacement
        )
    
    def get_register_form(self) -> FT:
        """DEPRECATED: Returns a message indicating registration is automatic."""
        return Div(
            H2("Registreerumine"),
            P("Süsteemi registreerumine toimub automaatselt esimesel sisselogimisel Smart-ID'ga."),
            A("Tagasi sisselogimise lehele", href="/login", cls="link"),
            cls="text-center space-y-4"
        )
        
    # --- MODIFIED process_login ---
    # Now accepts email and password directly from main.py handler
    # Marked async mainly for consistency, can be sync if no await inside
    async def process_login(self, request: Request, email: str, password: str):
        """ Processes login using parameters passed from the route handler. """
        # No need for await request.form() anymore
        print(f"--- DEBUG [AuthController]: process_login called with email: {email} ---") # Updated log
        try:
            # email and password arguments are already populated by FastHTML via main.py
            if not email or not password:
                print("--- DEBUG [AuthController]: Missing email or password argument ---")
                # This check might be redundant if main.py handler requires them
                return Span("Email and password arguments are required")

            print(f"--- DEBUG [AuthController]: Attempting to lookup user: {email} ---")
            user_data = self.users[email] # PK lookup
            print(f"--- DEBUG [AuthController]: User found: {user_data['email']} ---")

            print(f"--- DEBUG [AuthController]: Verifying password for {email} ---")
            if not verify_password(password, user_data['hashed_password']):
                print(f"--- DEBUG [AuthController]: Password verification FAILED for user '{email}'. ---")
                return Span("Email or password incorrect") # Return error Span for HTMX

            print(f"--- DEBUG [AuthController]: Password verification SUCCEEDED for user '{email}'. ---")
            request.session['authenticated'] = True
            request.session['user_email'] = user_data['email']
            # --- ADDED: Store user's role in the session ---
            request.session['role'] = normalize_role(user_data.get('role'), default=APPLICANT)
            print(f"--- DEBUG [AuthController]: Session set for {email} with role '{request.session['role']}'. Returning HX-Redirect. ---")
            # Return Response with HX-Redirect header for HTMX
            return Response(headers={'HX-Redirect': '/app'})

        except NotFoundError:
            print(f"--- DEBUG [AuthController]: User lookup FAILED (NotFoundError) for user: {email} ---")
            return Span("Email or password incorrect") # Return error Span for HTMX
        except Exception as e:
            print(f"--- ERROR [AuthController]: Unexpected error during login for {email}: {e} ---")
            traceback.print_exc()
            return Span("An unexpected error occurred during login.") # Return error Span for HTMX

    async def process_smart_id_login(self, request: Request, status_data: dict):
        """
        Processes a successful Smart-ID login, finds or creates a user, and sets the session.
        """
        try:
            # 1. Extract user data from the Smart-ID response
            result = status_data.get("result", {})
            cert = result.get("cert", {})
            subject_cert = cert.get("subject", {})

            # Extracting CN=SURNAME,GIVENNAME,SERIALNUMBER
            cn_parts = subject_cert.get("CN", "").split(',')
            if len(cn_parts) < 3:
                return Span("Invalid user certificate received from Smart-ID.")

            surname, given_name, national_id = cn_parts[0], cn_parts[1], cn_parts[2]
            full_name = f"{given_name} {surname}"
            
            # For now, let's use a placeholder email, as Smart-ID doesn't provide one.
            # You might need a strategy for handling emails, e.g., prompting the user later.
            email = f"{national_id}@kuts2.ee"

            print(f"--- DEBUG [AuthController]: Smart-ID success for {national_id} ({full_name}) ---")

            # 2. Find or create the user (Just-In-Time Provisioning)
            try:
                # We need to query by the new national_id_number column
                user_records = self.users("national_id_number = ?", [national_id])
                if not user_records: raise NotFoundError
                user_data = user_records[0]
                print(f"--- DEBUG [AuthController]: Found existing user by national ID: {user_data['email']} ---")

            except NotFoundError:
                print(f"--- DEBUG [AuthController]: User with national ID {national_id} not found. Creating new user. ---")
                # Note: We are not storing passwords anymore for Smart-ID users.
                new_user = {
                    "email": email,
                    "hashed_password": "", # No password
                    "full_name": full_name,
                    "birthday": None, # Smart-ID doesn't provide this, user can fill it in later.
                    "role": APPLICANT,
                    "national_id_number": national_id
                }
                self.users.insert(new_user, pk='email')
                user_data = new_user

            # 3. Create the user session
            request.session['authenticated'] = True
            request.session['user_email'] = user_data['email']
            request.session['role'] = normalize_role(user_data.get('role'), default=APPLICANT)
            
            print(f"--- DEBUG [AuthController]: Session created for {user_data['email']}. Redirecting to dashboard. ---")
            
            # 4. Return the redirect response
            return Response(headers={'HX-Redirect': '/dashboard'})

        except Exception as e:
            print(f"--- ERROR [AuthController]: Failed to process Smart-ID login: {e} ---")
            traceback.print_exc()
            return Span("An error occurred while finalizing your login. Please try again.")

    # --- MODIFIED process_registration ---
    # Now accepts all form fields directly
    # Marked async mainly for consistency
    async def process_registration(self, request: Request, email: str, password: str, confirm_password: str, full_name: str, birthday: str):
        """ Processes registration using parameters passed from the route handler. """
        # No need for await request.form() anymore
        print(f"--- DEBUG [AuthController]: process_registration called with email: {email} ---") # Updated log
        try:
            # Arguments (email, password, etc.) are already populated by FastHTML via main.py

            # Validation (can remain here or be done in main.py handler)
            if not all([email, password, confirm_password, full_name, birthday]):
                 print("--- DEBUG [AuthController]: Missing required registration arguments ---")
                 return Span("Please fill out all required fields.")

            if password != confirm_password:
                print("--- DEBUG [AuthController]: Registration passwords do not match ---")
                return Span("Passwords do not match") # Return error Span

            try:
                # Check if user already exists
                print(f"--- DEBUG [AuthController]: Checking if user exists: {email} ---")
                existing_user = self.users[email]
                print(f"Registration attempt failed: User '{email}' already exists.")
                return Span("User with this email already exists") # Return error Span
            except NotFoundError:
                print(f"--- DEBUG [AuthController]: User {email} does not exist, proceeding ---")
                pass

            hashed_password = get_password_hash(password)
            # --- ADDED: Include 'role' field on creation ---
            new_user = {
                "email": email,
                "hashed_password": hashed_password,
                "full_name": full_name,
                "birthday": birthday,
                "role": APPLICANT # Set default role
            }

            print(f"--- DEBUG [AuthController]: Inserting new user: {email} with role 'applicant' ---")
            self.users.insert(new_user, pk='email')
            print(f"Registration successful for user '{email}'.")

            request.session['authenticated'] = True
            request.session['user_email'] = email
            # --- ADDED: Set role in session immediately after registration ---
            request.session['role'] = APPLICANT
            print(f"--- DEBUG [AuthController]: Session set for {email}. Returning HX-Redirect. ---")
            # Return Response with HX-Redirect header for HTMX
            return Response(headers={'HX-Redirect': '/app'})

        except Exception as e:
            print(f"--- ERROR [AuthController] during registration for '{email}': {e}")
            traceback.print_exc()
            return Span("Registration failed due to an unexpected error.") # Return error Span

    def logout(self, request: Request):
        """ Clears the session and redirects to the login page. """
        print(f"Logging out user: {request.session.get('user_email')}") # Server log
        request.session.clear()
        # Use standard redirect for logout
        return RedirectResponse('/login', status_code=303)