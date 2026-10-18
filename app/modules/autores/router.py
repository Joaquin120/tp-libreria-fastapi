"""Endpoints HTTP del módulo de autores (Ejercicios 4 y 5)."""

from fastapi import APIRouter, Depends, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.modules.autores import service
from app.modules.autores.schemas import AutorCreate, AutorRead, AutorUpdate, LibroDelAutor

router = APIRouter(prefix="/autores", tags=["autores"])


@router.post(
    "/",
    response_model=AutorRead,
    status_code=status.HTTP_201_CREATED,
    summary="Alta de autor",
)
async def crear_autor(
    datos: AutorCreate,
    session: AsyncSession = Depends(get_session),
) -> AutorRead:
    return await service.crear_autor(session, datos)


@router.get(
    "/{autor_id}",
    response_model=AutorRead,
    summary="Detalle de un autor",
)
async def obtener_autor(
    autor_id: int,
    session: AsyncSession = Depends(get_session),
) -> AutorRead:
    """404 si no existe; 422 si el path no es entero (C-01)."""
    return await service.obtener_autor(session, autor_id)


@router.patch(
    "/{autor_id}",
    response_model=AutorRead,
    summary="Actualización parcial de un autor",
)
async def actualizar_autor(
    autor_id: int,
    datos: AutorUpdate,
    session: AsyncSession = Depends(get_session),
) -> AutorRead:
    """404 si no existe."""
    return await service.actualizar_autor(session, autor_id, datos)


@router.get(
    "/{autor_id}/libros",
    response_model=list[LibroDelAutor],
    summary="Libros del autor con su rol y orden",
)
async def listar_libros_del_autor(
    autor_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> list[LibroDelAutor]:
    """404 si el autor no existe; cada libro indica el `rol` y `orden` del autor."""
    return await service.listar_libros_del_autor(
        session, autor_id, limit=limit, offset=offset
    )
