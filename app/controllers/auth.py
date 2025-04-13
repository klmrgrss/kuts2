# controllers/auth.py

from fasthtml.common import *
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response # Import Response
#from fastlite.core import NotFoundError # Import specific exception for checking user existence

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
        
    def process_login(self, request: Request, email: str, password: str):
        """
        Processes a login attempt.
        Args:
            request: The Starlette request, used for session access.
            email: User's email from form.
            password: User's plain password from form.
        Returns:
            RedirectResponse on success, error Span on failure for HTMX.
        """
        try:
            # ** CHANGED: Use dictionary-style lookup by PK **
            user_data = self.users[email] 
        except NotFoundError:
            print(f"Login attempt failed: User '{email}' not found.") # Server log
            return Span("Email or password incorrect") # Return error message
            
        # Verify password
        if not verify_password(password, user_data['hashed_password']):
            print(f"Login attempt failed: Incorrect password for user '{email}'.") # Server log
            return Span("Email or password incorrect") # Return error message

        # --- Login successful ---
        print(f"Login successful for user '{email}'.") # Server log
        # Store authentication state in session
        request.session['authenticated'] = True
        request.session['user_email'] = user_data['email'] 
        # Add other user details if needed, but avoid storing sensitive info
        # request.session['user_full_name'] = user_data.get('full_name') 

        # Send HTMX redirect header
        # Redirecting to '/app' which should load the main authenticated view (e.g., dashboard)
        return Response(headers={'HX-Redirect': '/app'}) 
        # Note: If not using HTMX, would return RedirectResponse('/app', status_code=303)

    def process_registration(self, request: Request, email: str, password: str, confirm_password: str, full_name: str, birthday: str):
        """
        Processes a registration attempt.
        Args:
            request: The Starlette request, used for session access.
            email: User's email.
            password: User's plain password.
            confirm_password: Password confirmation.
            full_name: User's full name.
            birthday: User's birthday string (e.g., "YYYY-MM-DD").
        Returns:
            RedirectResponse on success, error Span on failure for HTMX.
        """
        if password != confirm_password:
            return Span("Passwords do not match") # Return error message

        # Check if user already exists
        try:
            # ** CHANGED: Use dictionary-style lookup by PK **
            existing_user = self.users[email] 
            # If lookup succeeds, user exists
            print(f"Registration attempt failed: User '{email}' already exists.") # Server log
            return Span("User with this email already exists") # Return error message
        except NotFoundError:
            # User does not exist, proceed with registration
            pass 

        try:
            # Hash the password
            hashed_password = get_password_hash(password)
            
            # Create new user record
            new_user = {
                "email": email,
                "hashed_password": hashed_password,
                "full_name": full_name,
                "birthday": birthday
            }
            
            # Insert into database
            self.users.insert(new_user, pk='email') # Specify PK explicitly if needed by insert
            
            # --- Registration successful ---
            print(f"Registration successful for user '{email}'.") # Server log
            # Log the user in immediately by setting session variables
            request.session['authenticated'] = True
            request.session['user_email'] = email

            # Send HTMX redirect header
            return Response(headers={'HX-Redirect': '/app'}) # Redirect to main app page
            # Note: If not using HTMX, would return RedirectResponse('/app', status_code=303)

        except Exception as e:
            print(f"ERROR during registration for '{email}': {e}") # Log the actual error
            # Optionally log traceback: import traceback; traceback.print_exc()
            return Span(f"Registration failed due to an unexpected error.") # Generic error for user

    def logout(self, request: Request):
        """ Clears the session and redirects to the login page. """
        print(f"Logging out user: {request.session.get('user_email')}") # Server log
        request.session.clear()
        # Use standard redirect for logout
        return RedirectResponse('/login', status_code=303)