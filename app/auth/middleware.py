"""Authentication middleware with legacy session support."""

from __future__ import annotations

import base64
import json
import os
from binascii import Error as BinasciiError
from typing import Any, Dict, Optional

from itsdangerous import BadSignature, Signer
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.types import ASGIApp


class AuthMiddleware(BaseHTTPMiddleware):
    """Ensure requests are authenticated while supporting legacy session cookies."""

    def __init__(self, app: ASGIApp, db, session_secret: Optional[str] = None):
        super().__init__(app)
        # All Smart-ID routes are public
        self.public_prefixes = ["/static/", "/auth/smart-id/"]
        self.public_exact_paths = ["/", "/logout", "/favicon.ico", "/test"]
        self.db = db
        self.session_secret = session_secret or os.environ.get("SESSION_SECRET_KEY")

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        path = request.url.path
        request.state.db = self.db  # Attach db to all requests
        # Allow public paths to proceed without any auth checks.
        if any(path.startswith(prefix) for prefix in self.public_prefixes) or path in self.public_exact_paths:
            return await call_next(request)

        # For all other non-public paths, check for an authenticated session.
        if not request.session.get("authenticated"):
            legacy_session = self._load_legacy_session(request)
            if legacy_session:
                session_store = request.scope.setdefault("session", {})
                session_store.update(legacy_session)
                for key, value in legacy_session.items():
                    request.session[key] = value
                request.state.legacy_session = legacy_session

        if not request.session.get("authenticated"):
            # If not authenticated, redirect to the main landing page to log in.
            return RedirectResponse(url="/", status_code=303)

        # If the user is authenticated, let the request proceed.
        # The route-specific `guard_request` function will now handle authorization (role checks).
        return await call_next(request)

    def _load_legacy_session(self, request: Request) -> Optional[Dict[str, Any]]:
        """Attempt to decode legacy signer-based session cookies."""

        raw_cookie = request.cookies.get("session")
        if not raw_cookie or not self.session_secret:
            return None

        signer = Signer(self.session_secret)
        try:
            unsigned = signer.unsign(raw_cookie)
            decoded = base64.b64decode(unsigned)
            payload = json.loads(decoded.decode("utf-8"))
        except (BadSignature, BinasciiError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
            return None

        if not isinstance(payload, dict):
            return None

        allowed_keys = {"authenticated", "user_email", "role"}
        session_subset = {key: payload[key] for key in allowed_keys if key in payload}

        if session_subset.get("authenticated"):
            return session_subset

        return None
