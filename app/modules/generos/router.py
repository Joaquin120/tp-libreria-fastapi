"""Endpoints HTTP del módulo de géneros (Ejercicios 4 y 5)."""

from fastapi import APIRouter, Depends, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.modules.generos import service
from app.modules.generos.schemas import GeneroCreate, GeneroRead
from app.modules.libros.schemas import LibroRead

router = APIRouter(prefix="/generos", tags=["generos"])


@router.post(
    "/",
    response_model=GeneroRead,
    status_code=status.HTTP_201_CREATED,
    summary="Alta de género",
)
async def crear_genero(
    datos: GeneroCreate,
    session: AsyncSession = Depends(get_session),
) -> GeneroRead:
    """Crea un género. 409 si el nombre ya existe (RN-01, RN-12)."""
    return await service.crear_genero(session, datos)


@router.get(
    "/",
    response_model=list[GeneroRead],
    summary="Listado paginado de géneros",
)
async def listar_generos(
    limit: int = Query(default=20, ge=1, le=100, description="Máximo de resultados (RN-10)"),
    offset: int = Query(default=0, ge=0, description="Desplazamiento para paginar (RN-10)"),
    session: AsyncSession = Depends(get_session),
) -> list[GeneroRead]:
    return await service.listar_generos(session, limit=limit, offset=offset)


@router.get(
    "/{genero_id}/libros",
    response_model=list[LibroRead],
    summary="Libros de un género",
)
async def listar_libros_genero(
    genero_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> list[LibroRead]:
    """404 si el género no existe; libros con editorial/género/autores resueltos."""
    return await service.listar_libros_genero(session, genero_id, limit=limit, offset=offset)
