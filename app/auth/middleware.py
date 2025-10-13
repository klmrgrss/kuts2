# /auth/middleware.py


from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.types import ASGIApp


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, db):
        super().__init__(app)
        # All Smart-ID routes are public
        self.public_prefixes = ["/static/", "/auth/smart-id/"]
        self.public_exact_paths = ["/", "/logout", "/favicon.ico", "/test"]
        self.db = db

    async def dispatch(
        self, request: Request,
        call_next: RequestResponseEndpoint
    ) -> Response:
        path = request.url.path
        request.state.db = self.db # Attach db to all requests

        # Allow public paths to proceed without any auth checks.
        if any(path.startswith(prefix) for prefix in self.public_prefixes) or path in self.public_exact_paths:
            return await call_next(request)

        # For all other non-public paths, check for an authenticated session.
        if not request.session.get("authenticated"):
            # If not authenticated, redirect to the main landing page to log in.
            return RedirectResponse(url="/", status_code=303)

        # If the user is authenticated, let the request proceed.
        # The route-specific `guard_request` function will now handle authorization (role checks).
        return await call_next(request)