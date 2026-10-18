"""Endpoints HTTP del módulo de clientes (Ejercicios 4, 5 y 6).

Códigos: 201 en POST, 200 en GET/PATCH, 404 inexistente, 409 conflicto
(RN-02 email único, RN-09 perfil único), 422 validación.
"""

from fastapi import APIRouter, Depends, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.modules.clientes import service
from app.modules.clientes.schemas import (
    ClienteCreate,
    ClienteRead,
    ClienteUpdate,
    PerfilClienteCreate,
    PerfilClienteRead,
    PerfilClienteUpdate,
)
from app.modules.ventas.schemas import VentaRead

router = APIRouter(prefix="/clientes", tags=["clientes"])


@router.post(
    "/",
    response_model=ClienteRead,
    status_code=status.HTTP_201_CREATED,
    summary="Alta de cliente",
)
async def crear_cliente(
    datos: ClienteCreate,
    session: AsyncSession = Depends(get_session),
) -> ClienteRead:
    """409 si el email ya existe (RN-02, delegado en la BD)."""
    return await service.crear_cliente(session, datos)


@router.get(
    "/{cliente_id}",
    response_model=ClienteRead,
    summary="Detalle de un cliente con su perfil",
)
async def obtener_cliente(
    cliente_id: int,
    session: AsyncSession = Depends(get_session),
) -> ClienteRead:
    """404 si no existe; perfil precargado con joinedload (1 a 1, RN-03)."""
    return await service.obtener_cliente(session, cliente_id)


@router.patch(
    "/{cliente_id}",
    response_model=ClienteRead,
    summary="Actualización parcial de un cliente",
)
async def actualizar_cliente(
    cliente_id: int,
    datos: ClienteUpdate,
    session: AsyncSession = Depends(get_session),
) -> ClienteRead:
    """404 si no existe; 409 si el email nuevo ya existe (RN-02)."""
    return await service.actualizar_cliente(session, cliente_id, datos)


@router.post(
    "/{cliente_id}/perfil",
    response_model=PerfilClienteRead,
    status_code=status.HTTP_201_CREATED,
    summary="Alta del perfil de un cliente (1 a 1)",
)
async def crear_perfil(
    cliente_id: int,
    datos: PerfilClienteCreate,
    session: AsyncSession = Depends(get_session),
) -> PerfilClienteRead:
    """404 si el cliente no existe; 409 si ya tenía perfil (RN-09, C-03)."""
    return await service.crear_perfil(session, cliente_id, datos)


@router.patch(
    "/{cliente_id}/perfil",
    response_model=PerfilClienteRead,
    summary="Actualización parcial del perfil de un cliente",
)
async def actualizar_perfil(
    cliente_id: int,
    datos: PerfilClienteUpdate,
    session: AsyncSession = Depends(get_session),
) -> PerfilClienteRead:
    """404 si el cliente no tiene perfil."""
    return await service.actualizar_perfil(session, cliente_id, datos)


@router.get(
    "/{cliente_id}/ventas",
    response_model=list[VentaRead],
    summary="Ventas de un cliente",
)
async def listar_ventas_cliente(
    cliente_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> list[VentaRead]:
    """404 si el cliente no existe; ventas con cliente y renglones resueltos (RN-03)."""
    return await service.listar_ventas_cliente(
        session, cliente_id, limit=limit, offset=offset
    )
