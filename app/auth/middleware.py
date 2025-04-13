# auth/middleware.py

# ... other imports ...
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.types import ASGIApp

class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        # Add "/files" to the list of paths that don't require login
        self.public_prefixes = ["/static", "/files"] # Modified
        self.public_exact_paths = ["/login", "/register", "/favicon.ico"] # Separated exact paths
        self.root_path = "/"
        self.protected_prefix = "/app"
        # Remove public_paths if using prefixes/exact lists now
        # self.public_paths = ["/login", "/register", "/static", "/favicon.ico", "/files"] # Old way

    async def dispatch(
        self, request: Request,
        call_next: RequestResponseEndpoint
    ) -> Response:
        path = request.url.path
        print(f"--- DEBUG [Middleware]: Path='{path}' ---")

        # --- NEW Check using prefixes ---
        if any(path.startswith(prefix) for prefix in self.public_prefixes):
             print(f"--- DEBUG [Middleware]: Allowing public prefix path '{path}' ---")
             return await call_next(request)
        # --- END NEW Check ---

        # --- Check exact public paths ---
        is_public_exact = (path == self.root_path) or any(path == p for p in self.public_exact_paths)
        if is_public_exact:
             print(f"--- DEBUG [Middleware]: Allowing exact public path '{path}' ---")
             return await call_next(request)
        # --- End Check exact ---

        # --- Temporary rule for /evaluator (keep if needed) ---
        if path.startswith("/evaluator"):
            print("--- DEBUG [Middleware]: Allowing /evaluator path during development ---")
            return await call_next(request)
        # --- End Temporary rule ---

        # --- Protected /app check (keep as is) ---
        if path.startswith(self.protected_prefix):
            print("--- DEBUG [Middleware]: Path requires authentication ---")
            is_authenticated = request.session.get("authenticated", False)
            if not is_authenticated:
                print("--- DEBUG [Middleware]: User NOT authenticated, redirecting to login ---")
                return RedirectResponse(url="/login", status_code=303)
            else:
                 print("--- DEBUG [Middleware]: User IS authenticated, proceeding ---")
                 return await call_next(request)

        # --- Fallback Redirect (keep as is) ---
        print(f"--- DEBUG [Middleware]: Path '{path}' not public/protected, redirecting to root ---")
        # Default behavior for non-matched paths - consider if this is desired
        # For now, keeping the redirect to root as originally intended
        return RedirectResponse(url="/", status_code=303)