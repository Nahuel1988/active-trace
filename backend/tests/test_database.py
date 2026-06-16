import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


pytestmark = pytest.mark.requires_db


class TestDatabaseConnection:
    async def test_select_one_returns_result(self, db_session: AsyncSession) -> None:
        result = await db_session.execute(text("SELECT 1 AS val"))
        row = result.one()
        assert row.val == 1

    async def test_session_closes_on_exception(self, db_session: AsyncSession) -> None:
        with pytest.raises(RuntimeError):
            async with db_session:
                await db_session.execute(text("SELECT 1"))
                raise RuntimeError("simulated failure")
        assert db_session.is_active or db_session.closed
