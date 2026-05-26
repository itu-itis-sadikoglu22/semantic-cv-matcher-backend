from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session

router = APIRouter()


@router.get("/db-test")
async def test_database_connection(
    db: AsyncSession = Depends(get_db_session),
):
    """
    Test database connectivity with a simple SQL query.
    """

    result = await db.execute(text("SELECT 1"))
    value = result.scalar_one()

    return {
        "status": "connected",
        "database_test_value": value,
    }