"""Signing browsers in: sessions kept in the store, held by the browser in a cookie.

The cookie is httpOnly, so no script on the page can read it, and SameSite=Lax, so other
sites' pages cannot make the browser send it with their forms; over HTTPS in production
it is Secure as well. On top of that every request that changes something must come
from the site's own origin (`origin_allowed`). A session lasts `SESSION_LIFETIME` after it
was last used; each renewal renews the cookie too.
"""

import ipaddress
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Annotated
from urllib.parse import SplitResult, urlsplit

from fastapi import Depends, Header, HTTPException, Request, Response
from fastapi.responses import JSONResponse

from eidolon.config import Settings
from eidolon.store import SESSION_LIFETIME, User

if TYPE_CHECKING:
    from eidolon.assembly import Backend

SESSION_COOKIE = "eidolon_session"

_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


def set_session_cookie(response: Response, token: str, settings: Settings) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=int(SESSION_LIFETIME.total_seconds()),
        path="/",
        httponly=True,
        samesite="lax",
        secure=settings.domain is not None,
    )


def clear_session_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        SESSION_COOKIE, path="/", httponly=True, samesite="lax", secure=settings.domain is not None
    )


def origin_allowed(
    origin: str | None, signed_in: bool, settings: Settings, host: str | None = None
) -> bool:
    """Whether a request that changes something may come from `origin`. Browsers always
    say where such a request comes from, so one that carries the session cookie must;
    one without the cookie gets nowhere anyway. In development any page on this machine
    is the site."""
    if origin is None:
        return not signed_in
    if settings.domain is not None:
        return origin == settings.public_origin
    try:
        parts = urlsplit(origin)
        if parts.scheme not in {"http", "https"} or not parts.hostname or parts.username:
            return False
        _ = parts.port
    except ValueError:
        return False
    # The page's own address is always the site, whatever hostname it was opened by: the LAN
    # address, the Tailscale one, or a name only that machine knows.
    if host and _same_host(parts, host):
        return True
    if parts.scheme == "http" and parts.hostname in _LOCAL_HOSTS:
        return True
    # Local development also accepts private network addresses, never arbitrary websites.
    return settings.dev_login and _private_host(parts.hostname)


def _same_host(parts: SplitResult, host: str) -> bool:
    """Whether the origin's scheme authority is the request's own `host` header."""
    try:
        target = urlsplit(f"{parts.scheme}://{host}")
        default = 443 if parts.scheme == "https" else 80
        return (
            parts.hostname == target.hostname
            and (parts.port or default) == (target.port or default)
        )
    except ValueError:
        return False


def _private_host(hostname: str | None) -> bool:
    """Whether `hostname` is a private address: the LAN, a Tailscale one, or a local name."""
    if not hostname:
        return False
    if hostname.endswith(".local") or hostname in _LOCAL_HOSTS:
        return True
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        return False
    return (
        address.is_private or address.is_loopback or address.is_link_local
        or address in ipaddress.ip_network("100.64.0.0/10")
    )


def session_middleware(
    settings: Settings,
) -> Callable[[Request, Callable[[Request], Awaitable[Response]]], Awaitable[Response]]:
    """Refuses requests that change something from other origins, and renews the cookie
    of a session that was renewed while answering the request."""

    async def middleware(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if request.method not in _SAFE_METHODS and not origin_allowed(
            request.headers.get("origin"),
            SESSION_COOKIE in request.cookies,
            settings,
            request.headers.get("host"),
        ):
            return JSONResponse({"detail": "请求来自其他网站，已拒绝"}, status_code=403)
        response = await call_next(request)
        if (token := getattr(request.state, "renewed_session", None)) is not None:
            set_session_cookie(response, token, settings)
        return response

    return middleware


async def session_user(request: Request) -> User | None:
    """The user whose session the request's cookie carries, if any; renews the session
    (and, through the session middleware, the cookie) now and then."""
    backend: "Backend" = request.app.state.backend
    token = request.cookies.get(SESSION_COOKIE)
    session = await backend.store.use_session(token, backend.clock()) if token else None
    if session is None:
        return None
    if session.renewed:
        request.state.renewed_session = token
    return session.user


async def signed_in_user(request: Request) -> User:
    """The signed-in user; 401 if the browser is not signed in, 403 if the user is banned
    (banning ends their sessions, so only a request under way when it did gets this)."""
    user = await session_user(request)
    if user is None:
        raise HTTPException(401, "请先登录")
    if user.banned_at is not None:
        raise HTTPException(403, "这位用户已被封禁")
    return user


SignedIn = Annotated[User, Depends(signed_in_user)]


CONSENT_REQUIRED = 428
"""The status of every request, save agreeing, signing out and deleting their data, from
a user who has not yet agreed to the privacy policy and terms of use."""


def current_user(user: SignedIn) -> str:
    """The signed-in user's id, once they have agreed to the privacy policy and terms of
    use; until then, `CONSENT_REQUIRED`."""
    if user.consented_at is None:
        raise HTTPException(CONSENT_REQUIRED, "请先阅读并同意隐私政策和使用条款")
    return user.id


UserId = Annotated[str, Depends(current_user)]

DeviceTimezone = Annotated[str | None, Header(alias="X-Timezone")]
"""The time zone the browser detected; the producer profile's own time zone overrides it."""
