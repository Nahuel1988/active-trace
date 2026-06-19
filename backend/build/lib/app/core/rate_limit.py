"""Rate limiting configuration using SlowAPI.

Task 9.1: Create a rate limiter abstraction for login throttling.

Design:
    - Default limiter uses **IP-based** key function via ``get_remote_address``.
    - Login endpoint uses a **custom key function** that combines IP AND email
      into a composite key ``"<ip>:<email>"``.
    - 5 requests per 60-second window (in-memory backend, SlowAPI default).
    - When exceeded → 429 Too Many Requests via ``RateLimitExceeded`` handler.

Usage in a router::

    from app.core.rate_limit import limiter, login_key_func, LOGIN_RATE_LIMIT

    @router.post("/auth/login")
    @limiter.limit(LOGIN_RATE_LIMIT, key_func=login_key_func)
    async def login(request: Request, payload: LoginRequest = Depends(...)):
        ...

The caller **must** populate ``request.state.login_email`` (via a middleware
or a FastAPI dependency that runs **before** the rate-limit check) so that
``login_key_func`` can build the composite key.

For the top-level app, register::

    from slowapi import _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# ---------------------------------------------------------------------------
# Limiter instance — IP-based by default
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address)

# ---------------------------------------------------------------------------
# Rate-limit constants
# ---------------------------------------------------------------------------
LOGIN_RATE_LIMIT = "5/minute"
"""Maximum login attempts per rate-limit window per key (IP + email)."""


# ---------------------------------------------------------------------------
# Key helpers
# ---------------------------------------------------------------------------

def login_rate_limit_key(ip: str, email: str) -> str:
    """Combine IP and email into a composite rate-limit key.

    Args:
        ip: Client IP address.
        email: Email address from the login request.

    Returns:
        A colon-separated key ``"<ip>:<email>"``.
    """
    return f"{ip}:{email}"


def _login_key_func(request) -> str:  # type: ignore[type-arg]
    """SlowAPI-compatible key function for the login endpoint.

    Extracts the client IP via ``get_remote_address`` and reads the email
    from ``request.state.login_email`` (set by a dependency that runs before
    the rate-limit check).

    Falls back to ``"unknown"`` if the email has not been populated.

    The parameter **must** be named ``request`` so that SlowAPI's
    ``__evaluate_limits`` detects it and passes the ``Request`` object.
    """
    ip = get_remote_address(request)
    email = getattr(request.state, "login_email", "unknown")
    return login_rate_limit_key(ip, email)


# Singleton key-function instance for reuse in the login route decorator.
login_key_func = _login_key_func
