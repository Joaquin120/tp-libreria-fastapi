"""Endpoints HTTP del módulo de editoriales (Ejercicios 4 y 5).

Códigos: 201 en POST, 200 en GET/PATCH, 404 inexistente, 409 conflicto
(unicidad/FK), 422 validación (path no entero, body inválido, paginación).
"""

from fastapi import APIRouter, Depends, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.modules.editoriales import service
from app.modules.editoriales.schemas import EditorialCreate, EditorialRead, EditorialUpdate
from app.modules.libros.schemas import LibroRead

router = APIRouter(prefix="/editoriales", tags=["editoriales"])


@router.post(
    "/",
    response_model=EditorialRead,
    status_code=status.HTTP_201_CREATED,
    summary="Alta de editorial",
)
async def crear_editorial(
    datos: EditorialCreate,
    session: AsyncSession = Depends(get_session),
) -> EditorialRead:
    """Crea una editorial. 409 si el nombre ya existe (RN-01, RN-12)."""
    return await service.crear_editorial(session, datos)


@router.get(
    "/",
    response_model=list[EditorialRead],
    summary="Listado paginado de editoriales",
)
async def listar_editoriales(
    limit: int = Query(default=20, ge=1, le=100, description="Máximo de resultados (RN-10)"),
    offset: int = Query(default=0, ge=0, description="Desplazamiento para paginar (RN-10)"),
    session: AsyncSession = Depends(get_session),
) -> list[EditorialRead]:
    return await service.listar_editoriales(session, limit=limit, offset=offset)


@router.get(
    "/{editorial_id}",
    response_model=EditorialRead,
    summary="Detalle de una editorial",
)
async def obtener_editorial(
    editorial_id: int,
    session: AsyncSession = Depends(get_session),
) -> EditorialRead:
    """404 si no existe; 422 si el path no es entero (C-01)."""
    return await service.obtener_editorial(session, editorial_id)


@router.patch(
    "/{editorial_id}",
    response_model=EditorialRead,
    summary="Actualización parcial de una editorial",
)
async def actualizar_editorial(
    editorial_id: int,
    datos: EditorialUpdate,
    session: AsyncSession = Depends(get_session),
) -> EditorialRead:
    """404 si no existe; 409 si el nombre nuevo ya pertenece a otra."""
    return await service.actualizar_editorial(session, editorial_id, datos)


@router.get(
    "/{editorial_id}/libros",
    response_model=list[LibroRead],
    summary="Libros de una editorial",
)
async def listar_libros_editorial(
    editorial_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> list[LibroRead]:
    """404 si la editorial no existe; libros con editorial/género/autores resueltos."""
    return await service.listar_libros_editorial(
        session, editorial_id, limit=limit, offset=offset
    )
