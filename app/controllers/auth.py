# controllers/auth.py

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
        """Returns the login form using MonsterUI components."""
        # Using LabelInput for combined label and input
        return Form(
            H2("Login"),
            LabelInput(label="Email", id="email", name="email", type="email", placeholder="you@example.com", required=True),
            LabelInput(label="Password", id="password", name="password", type="password", placeholder="Password", required=True),
            # Span to display errors returned from POST handler
            Span(id="login-error", cls="text-red-500"), 
            Button("Login", type="submit"),
            Hr(cls="my-4"), # Add margin to separator
            P("Want to create an Account? ", A("Register", href="/register")), # Assumes /register route exists
            # HTMX attributes for form submission
            method="post", 
            action="/login", # Submit to the /login POST route
            hx_post="/login",
            hx_target="#login-error", # Target the span for error messages
            hx_swap="innerHTML", # Replace content of error span
            cls="space-y-4" # Add spacing between form elements
        )
    
    def get_register_form(self) -> FT:
        """Returns the registration form using MonsterUI components."""
        return Form(
            H2("Register"),
            LabelInput(label="Full Name", id="full_name", name="full_name", placeholder="Your Full Name", required=True),
            LabelInput(label="Email", id="email", name="email", type="email", placeholder="you@example.com", required=True),
            LabelInput(label="Birthday", id="birthday", name="birthday", type="date", required=True), # Added Birthday
            LabelInput(label="Password", id="password", name="password", type="password", placeholder="Password", required=True),
            LabelInput(label="Confirm Password", id="confirm_password", name="confirm_password", type="password", placeholder="Confirm Password", required=True),
            # Span to display errors
            Span(id="register-error", cls="text-red-500"), 
            Button("Register", type="submit"),
            Hr(cls="my-4"),
            P("Already have an account? ", A("Login", href="/login")), # Assumes /login route exists
            # HTMX attributes
            method="post",
            action="/register", # Submit to the /register POST route
            hx_post="/register",
            hx_target="#register-error", # Target the span for error messages
            hx_swap="innerHTML", 
            cls="space-y-4"
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