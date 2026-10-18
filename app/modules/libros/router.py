"""Endpoints HTTP del módulo de libros (Ejercicios 4, 5 y 6).

Códigos: 201 en POST, 200 en GET/PATCH, 404 inexistente, 409 conflicto
(ISBN/FK, delegado en la BD), 422 validación (RN-10, C-01).
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.modules.libros import service
from app.modules.libros.schemas import LibroCreate, LibroRead, LibroUpdate

router = APIRouter(prefix="/libros", tags=["libros"])


@router.post(
    "/",
    response_model=LibroRead,
    status_code=status.HTTP_201_CREATED,
    summary="Alta de libro con sus autorías",
)
async def crear_libro(
    datos: LibroCreate,
    session: AsyncSession = Depends(get_session),
) -> LibroRead:
    """Inserta libro + autorías SIN consultas previas; 409 si el ISBN está
    repetido o si la editorial/género/autor no existen (RN-01, RN-12)."""
    return await service.crear_libro(session, datos)


@router.get(
    "/",
    response_model=list[LibroRead],
    summary="Listado de libros con filtros opcionales",
)
async def listar_libros(
    limit: int = Query(default=20, ge=1, le=100, description="Máximo de resultados (RN-10)"),
    offset: int = Query(default=0, ge=0, description="Desplazamiento para paginar (RN-10)"),
    titulo: Optional[str] = Query(
        default=None,
        description="Filtro insensible a mayúsculas con ilike y parámetro ligado (RN-11)",
    ),
    genero_id: Optional[int] = Query(
        default=None, description="Filtro exacto por género"
    ),
    session: AsyncSession = Depends(get_session),
) -> list[LibroRead]:
    """Libros con editorial, género y autores ya resueltos (sin N+1, RN-03)."""
    return await service.listar_libros(
        session, limit=limit, offset=offset, titulo=titulo, genero_id=genero_id
    )


@router.get(
    "/{libro_id}",
    response_model=LibroRead,
    summary="Detalle de un libro",
)
async def obtener_libro(
    libro_id: int,
    session: AsyncSession = Depends(get_session),
) -> LibroRead:
    """404 si no existe; 422 si el path no es entero (C-01).

    Respuesta en cantidad FIJA de consultas (C-07): 1 para el libro con
    editorial/género + 1 para las autorías con sus autores.
    """
    return await service.obtener_libro(session, libro_id)


@router.patch(
    "/{libro_id}",
    response_model=LibroRead,
    summary="Actualización parcial de un libro",
)
async def actualizar_libro(
    libro_id: int,
    datos: LibroUpdate,
    session: AsyncSession = Depends(get_session),
) -> LibroRead:
    """404 si no existe; 409 si el ISBN choca u otra FK falla; 422 si el body es inválido."""
    return await service.actualizar_libro(session, libro_id, datos)
