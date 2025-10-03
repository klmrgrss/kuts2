"""Declarative authorization helpers for route handlers."""
from __future__ import annotations

import inspect
from functools import wraps
from typing import Any, Awaitable, Callable, Iterable, Tuple

from fastlite import NotFoundError
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

from auth.roles import ADMIN, ALL_ROLES, allowed_roles, describe_roles, normalize_role

GuardedHandler = Callable[..., Awaitable[Any] | Any]


def get_current_user(request: Request) -> dict[str, Any] | None:
    """Retrieve the current user record using the request-bound database."""
    email = request.session.get("user_email")
    if not email:
        return None

    db = getattr(request.state, "db", None)
    if db is None:
        return None

    try:
        return db.t.users[email]
    except NotFoundError:
        return None


def require_role(*roles: str) -> Callable[[GuardedHandler], GuardedHandler]:
    """Decorator that restricts a route to the supplied roles (admins always pass)."""

    allowed = allowed_roles(*roles) if roles else ALL_ROLES

    def decorator(handler: GuardedHandler) -> GuardedHandler:
        @wraps(handler)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            request = _extract_request(args, kwargs)
            response_or_user = _check_access(request, allowed)
            if isinstance(response_or_user, Response):
                return response_or_user

            kwargs.setdefault("current_user", response_or_user)
            result = handler(*args, **kwargs)
            if inspect.isawaitable(result):
                return await result
            return result

        @wraps(handler)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            request = _extract_request(args, kwargs)
            response_or_user = _check_access(request, allowed)
            if isinstance(response_or_user, Response):
                return response_or_user

            kwargs.setdefault("current_user", response_or_user)
            return handler(*args, **kwargs)

        if inspect.iscoroutinefunction(handler):
            return async_wrapper  # type: ignore[return-value]
        return sync_wrapper  # type: ignore[return-value]

    return decorator


def _extract_request(args: Tuple[Any, ...], kwargs: dict[str, Any]) -> Request:
    if args:
        candidate = args[0]
        if isinstance(candidate, Request):
            return candidate
    request = kwargs.get("request")
    if isinstance(request, Request):
        return request
    raise RuntimeError("Route handler must receive a starlette Request as the first argument")


def _check_access(request: Request, allowed: Iterable[str]) -> Response | dict[str, Any]:
    if not request.session.get("authenticated"):
        return RedirectResponse("/login", status_code=303)

    user = get_current_user(request)
    if not user:
        request.session.clear()
        return RedirectResponse("/login", status_code=303)

    role = normalize_role(user.get("role"))
    if role == ADMIN or role in allowed:
        request.state.current_user = user
        return user

    detail = (
        "Forbidden: required role one of {roles}, but current role is '{current}'."
        .format(roles=describe_roles(allowed), current=role)
    )
    return Response(detail, status_code=403)


def guard_request(request: Request, *roles: str) -> Response | dict[str, Any]:
    """Utility to enforce access rules imperatively within a route."""

    allowed = allowed_roles(*roles) if roles else ALL_ROLES
    return _check_access(request, allowed)
