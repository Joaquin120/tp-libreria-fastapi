from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session

router = APIRouter(prefix="/health", tags=["health"])


@router.get(
    "/live",
    status_code=status.HTTP_200_OK,
    summary="Liveness: la app está viva (sin tocar la base de datos)",
)
async def live() -> dict[str, str]:
    return {"estado": "vivo"}


@router.get(
    "/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness: verifica la conexión a la base de datos",
)
async def ready(session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    await session.exec(text("SELECT 1"))
    return {"estado": "listo", "base_datos": "conectada"}
