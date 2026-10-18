"""Endpoints HTTP del módulo de ventas (Ejercicios 4, 5, 6 y 7).

RN-08: NO existe PATCH/PUT de ventas (son inmutables).

Códigos: 201 en POST, 200 en GET, 404 inexistente, 409 conflicto
(libro/cliente inexistente, caso C-05), 422 validación (RN-05).
"""

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.modules.ventas import service
from app.modules.ventas.schemas import VentaCreate, VentaRead

router = APIRouter(prefix="/ventas", tags=["ventas"])


@router.post(
    "/",
    response_model=VentaRead,
    status_code=status.HTTP_201_CREATED,
    summary="Alta de venta con sus renglones (RN-04, RN-06, RN-07)",
)
async def crear_venta(
    datos: VentaCreate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> VentaRead:
    """Precios copiados del servidor y total calculado en el servidor.

    409 si el libro o el cliente no existen (C-05); 422 si `renglones` está
    vacío o repite un libro (RN-05). Agenda el comprobante en background
    (Ejercicio 7): se ejecuta DESPUÉS de responder.
    """
    return await service.crear_venta(session, datos, background_tasks)


@router.get(
    "/",
    response_model=list[VentaRead],
    summary="Listado paginado de ventas",
)
async def listar_ventas(
    limit: int = Query(default=20, ge=1, le=100, description="Máximo de resultados (RN-10)"),
    offset: int = Query(default=0, ge=0, description="Desplazamiento para paginar (RN-10)"),
    session: AsyncSession = Depends(get_session),
) -> list[VentaRead]:
    return await service.listar_ventas(session, limit=limit, offset=offset)


@router.get(
    "/{venta_id}",
    response_model=VentaRead,
    summary="Detalle de una venta",
)
async def obtener_venta(
    venta_id: int,
    session: AsyncSession = Depends(get_session),
) -> VentaRead:
    """404 si no existe; 422 si el path no es entero (C-01).

    Respuesta en cantidad FIJA de consultas (C-07): 1 para la venta con su
    cliente + 1 para los renglones con sus libros.
    """
    return await service.obtener_venta(session, venta_id)
