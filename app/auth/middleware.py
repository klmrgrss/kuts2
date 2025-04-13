# In gem-app/app/auth/middleware.py

# ... other imports ...
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.types import ASGIApp

class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.public_prefixes = ["/static", "/files"]
        self.public_exact_paths = ["/", "/login", "/register", "/logout", "/favicon.ico", "/test"]
        self.root_path = "/"
        self.protected_prefix = "/app"

    async def dispatch(
        self, request: Request,
        call_next: RequestResponseEndpoint
    ) -> Response:
        path = request.url.path
        method = request.method # <-- Get the request method

        # +++ ADD Enhanced Debugging +++
        print(f"--- DEBUG [Middleware]: START Dispatch - Method='{method}', Path='{path}' ---")

        # +++ ADD Explicit Check for POST /login & /register +++
        if method == "POST" and path in ["/login", "/register"]:
            print(f"--- DEBUG [Middleware]: Explicitly allowing {method} {path} - Calling next handler ---")
            # Directly call the next handler in the chain (should be the router)
            return await call_next(request)
        # +++ END Explicit Check +++

        # --- Original Checks (now only run if the explicit check above didn't match) ---
        if any(path.startswith(prefix) for prefix in self.public_prefixes):
             print(f"--- DEBUG [Middleware]: Allowing public prefix path '{path}' ---")
             return await call_next(request)

        is_public_exact = (path == self.root_path) or any(path == p for p in self.public_exact_paths)
        if is_public_exact:
             print(f"--- DEBUG [Middleware]: Allowing exact public path '{path}' ---")
             return await call_next(request)

        if path.startswith("/evaluator"):
            print("--- DEBUG [Middleware]: Allowing /evaluator path during development ---")
            return await call_next(request)

        if path.startswith(self.protected_prefix):
            print("--- DEBUG [Middleware]: Path requires authentication ---")
            is_authenticated = request.session.get("authenticated", False)
            if not is_authenticated:
                print("--- DEBUG [Middleware]: User NOT authenticated, redirecting to login ---")
                return RedirectResponse(url="/login", status_code=303)
            else:
                 print("--- DEBUG [Middleware]: User IS authenticated, proceeding ---")
                 return await call_next(request)

        # --- Fallback Redirect ---
        print(f"--- DEBUG [Middleware]: Path '{path}' not public/protected/POST-auth, redirecting to root ---")
        return RedirectResponse(url="/", status_code=303)