import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app


class TestAppStartup:
    async def test_app_creates_without_error(self) -> None:
        app = create_app()
        assert app.title == "activia-trace"

    async def test_app_starts_and_responds(self) -> None:
        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200
