# /auth/middleware.py


from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.types import ASGIApp

class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.public_prefixes = ["/static/js/", "/files/download"]
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
            return await call_next(request)

        if any(path.startswith(prefix) for prefix in self.public_prefixes):
             return await call_next(request)

        is_public_exact = (path == self.root_path) or any(path == p for p in self.public_exact_paths)
        if is_public_exact:
             return await call_next(request)

        is_authenticated = request.session.get("authenticated", False)
        user_role = request.session.get("role")

        if path.startswith("/evaluator"):
            print("--- DEBUG [Middleware]: Path is under /evaluator, requires 'evaluator' role ---")
            if not is_authenticated:
                return RedirectResponse(url="/login", status_code=303)
            if user_role != 'evaluator':
                return RedirectResponse(url="/dashboard", status_code=303)
            return await call_next(request)

        if path.startswith("/files/view"):
            if not is_authenticated:
                return RedirectResponse(url="/login", status_code=303)
            return await call_next(request)

        if path.startswith(self.protected_prefix):
            if not is_authenticated:
                return RedirectResponse(url="/login", status_code=303)
            
            # --- THE FIX: Use a session flag instead of Referer header ---
            is_htmx_request = 'HX-Request' in request.headers
            has_visited_dashboard = request.session.get('visited_dashboard', False)
            
            if not is_htmx_request and not has_visited_dashboard:
                print(f"--- DEBUG [Middleware]: Full page load to '{path}' without dashboard visit. Redirecting. ---")
                return RedirectResponse(url="/dashboard", status_code=303)
            
            return await call_next(request)

        if path.startswith("/dashboard"):
            if not is_authenticated:
                return RedirectResponse(url="/login", status_code=303)
            return await call_next(request)

        print(f"--- DEBUG [Middleware]: Path '{path}' not handled, redirecting to root ---")
        return RedirectResponse(url="/", status_code=303)