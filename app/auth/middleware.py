# /auth/middleware.py


from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.types import ASGIApp

class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        # --- THE FIX: Make the '/files' prefix more specific ---
        # Changed "/files" to "/files/download" to avoid catching "/files/view"
        self.public_prefixes = ["/static", "/files/download"]
        self.public_exact_paths = ["/", "/login", "/register", "/logout", "/favicon.ico", "/test"]
        self.root_path = "/"
        self.protected_prefix = "/app"

    async def dispatch(
        self, request: Request,
        call_next: RequestResponseEndpoint
    ) -> Response:
        path = request.url.path
        method = request.method

        print(f"--- DEBUG [Middleware]: START Dispatch - Method='{method}', Path='{path}' ---")

        if method == "POST" and path in ["/login", "/register"]:
            print(f"--- DEBUG [Middleware]: Explicitly allowing {method} {path} - Calling next handler ---")
            return await call_next(request)

        # This check will now correctly ignore '/files/view/...'
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

        # The request for '/files/view/...' does not start with '/app',
        # so we need to add a condition to let it pass through to the router.
        # A simple way is to check if it's a file viewing request.
        if path.startswith("/files/view"):
            print("--- DEBUG [Middleware]: Path is for file viewing, requires authentication check ---")
            is_authenticated = request.session.get("authenticated", False)
            if not is_authenticated:
                print("--- DEBUG [Middleware]: User NOT authenticated for file view, redirecting to login ---")
                return RedirectResponse(url="/login", status_code=303)
            else:
                 print("--- DEBUG [Middleware]: User IS authenticated for file view, proceeding ---")
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

        print(f"--- DEBUG [Middleware]: Path '{path}' not handled, redirecting to root ---")
        return RedirectResponse(url="/", status_code=303)