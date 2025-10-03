# /auth/middleware.py


from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.types import ASGIApp


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, db):
        super().__init__(app)
        self.public_prefixes = ["/static/js/", "/files/download"]
        self.public_exact_paths = ["/", "/login", "/register", "/logout", "/favicon.ico", "/test"]
        self.root_path = "/"
        self.protected_prefix = "/app"
        self.db = db

    async def dispatch(
        self, request: Request,
        call_next: RequestResponseEndpoint
    ) -> Response:
        path = request.url.path
        method = request.method

        print(f"--- DEBUG [Middleware]: START Dispatch - Method='{method}', Path='{path}' ---")

        request.state.db = self.db

        if method == "POST" and path in ["/login", "/register"]:
            return await call_next(request)

        if any(path.startswith(prefix) for prefix in self.public_prefixes):
             return await call_next(request)

        is_public_exact = (path == self.root_path) or any(path == p for p in self.public_exact_paths)
        if is_public_exact:
             return await call_next(request)

        is_authenticated = request.session.get("authenticated", False)
        if path.startswith("/files/view"):
            if not is_authenticated:
                return RedirectResponse(url="/login", status_code=303)
            return await call_next(request)

        if path.startswith(self.protected_prefix):
            if not is_authenticated:
                return RedirectResponse(url="/login", status_code=303)

            return await call_next(request)

        if path.startswith("/dashboard"):
            if not is_authenticated:
                return RedirectResponse(url="/login", status_code=303)
            return await call_next(request)

        return await call_next(request)