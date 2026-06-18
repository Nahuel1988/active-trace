"""Tests for rate limiting — TDD: RED → GREEN → TRIANGULATE.

Task 9.2: Apply rate limiting to login endpoint.
"""

import pytest
from fastapi import FastAPI, APIRouter, Depends, Request
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.rate_limit import login_key_func, LOGIN_RATE_LIMIT


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _LoginRequest(BaseModel):
    """Minimal login payload for testing rate limits."""
    email: str
    password: str


async def _inject_email(request: Request, payload: _LoginRequest) -> _LoginRequest:
    """Dependency: capture login email into request.state before rate-limit check."""
    request.state.login_email = payload.email
    return payload


# ---------------------------------------------------------------------------
# Fixtures — fresh app + limiter per test to avoid cross-contamination
# ---------------------------------------------------------------------------

@pytest.fixture
def app() -> FastAPI:
    """Create a fresh FastAPI app with a fresh rate limiter for each test."""
    limiter = Limiter(key_func=get_remote_address)

    app = FastAPI()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    auth_router = APIRouter()

    @auth_router.post("/auth/login")
    @limiter.limit(LOGIN_RATE_LIMIT, key_func=login_key_func)
    async def login(
        request: Request,
        payload: _LoginRequest = Depends(_inject_email),
    ) -> dict:
        return {"message": "ok"}

    app.include_router(auth_router, prefix="/api/v1")
    return app


@pytest.fixture
async def client(app: FastAPI) -> AsyncClient:
    """AsyncTestClient bound to the test app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestLoginRateLimit:
    """Rate-limiting behaviour for the login endpoint (Task 9.2)."""

    URL = "/api/v1/auth/login"
    PAYLOAD = {"email": "alice@example.com", "password": "secret"}

    async def test_allow_up_to_five_requests(self, client: AsyncClient) -> None:
        """RED→GREEN: 5 requests within the window → all return 200."""
        for i in range(5):
            resp = await client.post(self.URL, json=self.PAYLOAD)
            assert resp.status_code == 200, (
                f"Attempt {i + 1} expected 200, got {resp.status_code}: {resp.text}"
            )

    async def test_block_sixth_request(self, client: AsyncClient) -> None:
        """RED→GREEN: 6th request in the same window → 429."""
        for _ in range(5):
            await client.post(self.URL, json=self.PAYLOAD)

        resp = await client.post(self.URL, json=self.PAYLOAD)
        assert resp.status_code == 429, f"Expected 429, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "error" in data

    async def test_different_email_separate_counter(self, client: AsyncClient) -> None:
        """TRIANGULATE: different email → different rate-limit counter."""
        # Exhaust limit for alice
        for _ in range(5):
            await client.post(
                self.URL,
                json={"email": "alice@example.com", "password": "x"},
            )
        # alice's 6th → 429
        resp_alice = await client.post(
            self.URL,
            json={"email": "alice@example.com", "password": "x"},
        )
        assert resp_alice.status_code == 429

        # Bob should still be allowed (separate key)
        for i in range(5):
            resp = await client.post(
                self.URL,
                json={"email": "bob@example.com", "password": "x"},
            )
            assert resp.status_code == 200, (
                f"Bob attempt {i + 1} expected 200, got {resp.status_code}"
            )

    async def test_rate_limit_returns_json_error(self, client: AsyncClient) -> None:
        """TRIANGULATE: 429 response has expected error shape."""
        for _ in range(5):
            await client.post(self.URL, json=self.PAYLOAD)

        resp = await client.post(self.URL, json=self.PAYLOAD)
        assert resp.status_code == 429
        assert resp.headers.get("content-type", "").startswith("application/json")
        body = resp.json()
        assert "error" in body
        assert "rate limit" in body["error"].lower()
