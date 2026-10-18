"""Lógica de negocio del módulo de clientes (Ejercicios 4, 5 y 6).

Reglas clave:
- RN-02: `email` único -> alta directa + `IntegrityError` -> 409.
- RN-09: perfil único por cliente (UNIQUE en `perfil_cliente.cliente_id`) ->
  alta directa + `IntegrityError` -> 409. En `POST /clientes/{id}/perfil`
  SÍ se verifica antes que el cliente exista (404 si no existe).
- Sin N+1 (RN-03): `Cliente.perfil` (1 a 1) siempre se trae con `joinedload`.
"""

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import joinedload
from sqlmodel import select

from app.core.pagination import validar_paginacion
from app.modules.clientes.models import Cliente, PerfilCliente
from app.modules.clientes.schemas import (
    ClienteCreate,
    ClienteRead,
    ClienteUpdate,
    PerfilClienteCreate,
    PerfilClienteRead,
    PerfilClienteUpdate,
)
from app.modules.ventas.models import Venta
from app.modules.ventas.schemas import VentaRead
from app.modules.ventas.service import carga_completa_ventas, venta_a_read


def _a_cliente_read(cliente: Cliente) -> ClienteRead:
    """DTO de cliente con su perfil (objeto o None, nunca lista)."""
    perfil = (
        PerfilClienteRead.model_validate(cliente.perfil)
        if cliente.perfil is not None
        else None
    )
    return ClienteRead(
        id=cliente.id,
        nombre=cliente.nombre,
        email=cliente.email,
        perfil=perfil,
    )


def _carga_perfil(stmt):
    """`joinedload` de la relación 1 a 1 para evitar lazy loading (RN-03)."""
    return stmt.options(joinedload(Cliente.perfil))


async def crear_cliente(session: AsyncSession, datos: ClienteCreate) -> ClienteRead:
    """Alta de cliente: insert directo; `email` repetido -> 409 (RN-02)."""
    cliente = Cliente.model_validate(datos)
    session.add(cliente)
    try:
        await session.commit()
    except IntegrityError:
        # RN-12: mensaje propio, sin exponer constraints ni tablas.
        await session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Ya existe un cliente con ese email",
        )
    resultado = await session.exec(
        _carga_perfil(select(Cliente).where(Cliente.id == cliente.id))
    )
    return _a_cliente_read(resultado.one())


async def listar_clientes(
    session: AsyncSession,
    limit: int = 20,
    offset: int = 0,
) -> list[ClienteRead]:
    """Listado paginado (RN-10) con el perfil precargado en la misma consulta."""
    validar_paginacion(limit, offset)
    resultado = await session.exec(
        _carga_perfil(
            select(Cliente).order_by(Cliente.id).limit(limit).offset(offset)
        )
    )
    return [_a_cliente_read(cliente) for cliente in resultado.all()]


async def obtener_cliente(session: AsyncSession, cliente_id: int) -> ClienteRead:
    """Detalle por id con perfil precargado; 404 si no existe."""
    resultado = await session.exec(
        _carga_perfil(select(Cliente).where(Cliente.id == cliente_id))
    )
    cliente = resultado.one_or_none()
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return _a_cliente_read(cliente)


async def actualizar_cliente(
    session: AsyncSession,
    cliente_id: int,
    datos: ClienteUpdate,
) -> ClienteRead:
    """Actualización parcial con `exclude_unset`; email repetido -> 409."""
    cliente = await session.get(Cliente, cliente_id)
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    campos = datos.model_dump(exclude_unset=True)
    for nombre, valor in campos.items():
        setattr(cliente, nombre, valor)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Ya existe un cliente con ese email",
        )
    resultado = await session.exec(
        _carga_perfil(select(Cliente).where(Cliente.id == cliente_id))
    )
    return _a_cliente_read(resultado.one())


async def eliminar_cliente(session: AsyncSession, cliente_id: int) -> None:
    """Baja; si tiene ventas la BD rechaza por FK -> 409."""
    cliente = await session.get(Cliente, cliente_id)
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    await session.delete(cliente)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=409,
            detail="No se puede eliminar el cliente porque tiene ventas asociadas",
        )


async def crear_perfil(
    session: AsyncSession,
    cliente_id: int,
    datos: PerfilClienteCreate,
) -> PerfilClienteRead:
    """Alta de perfil para un cliente (RN-09).

    - Si el cliente NO existe -> 404 (única verificación previa permitida).
    - Si el cliente YA tiene perfil, la BD rechaza por el UNIQUE de
      `cliente_id` -> 409. No se consulta antes: se delega en la BD.
    """
    cliente = await session.get(Cliente, cliente_id)
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    perfil = PerfilCliente(cliente_id=cliente_id, **datos.model_dump())
    session.add(perfil)
    try:
        await session.commit()
    except IntegrityError:
        # RN-09/RN-12: mensaje propio, sin exponer el UNIQUE ni el constraint.
        await session.rollback()
        raise HTTPException(
            status_code=409,
            detail="El cliente ya tiene un perfil registrado",
        )
    await session.refresh(perfil)
    return PerfilClienteRead.model_validate(perfil)


async def obtener_perfil(session: AsyncSession, cliente_id: int) -> PerfilClienteRead:
    """Detalle del perfil de un cliente; 404 si no existe ni el cliente ni el perfil."""
    resultado = await session.exec(
        select(PerfilCliente).where(PerfilCliente.cliente_id == cliente_id)
    )
    perfil = resultado.one_or_none()
    if perfil is None:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
    return PerfilClienteRead.model_validate(perfil)


async def actualizar_perfil(
    session: AsyncSession,
    cliente_id: int,
    datos: PerfilClienteUpdate,
) -> PerfilClienteRead:
    """Actualización parcial del perfil con `exclude_unset`; 404 si no existe."""
    resultado = await session.exec(
        select(PerfilCliente).where(PerfilCliente.cliente_id == cliente_id)
    )
    perfil = resultado.one_or_none()
    if perfil is None:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")

    campos = datos.model_dump(exclude_unset=True)
    for nombre, valor in campos.items():
        setattr(perfil, nombre, valor)

    await session.commit()
    await session.refresh(perfil)
    return PerfilClienteRead.model_validate(perfil)


async def eliminar_perfil(session: AsyncSession, cliente_id: int) -> None:
    """Baja del perfil; 404 si el cliente no tiene perfil."""
    resultado = await session.exec(
        select(PerfilCliente).where(PerfilCliente.cliente_id == cliente_id)
    )
    perfil = resultado.one_or_none()
    if perfil is None:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")

    await session.delete(perfil)
    await session.commit()


async def listar_ventas_cliente(
    session: AsyncSession,
    cliente_id: int,
    limit: int = 20,
    offset: int = 0,
) -> list[VentaRead]:
    """Ventas de un cliente con sus renglones; 404 si el cliente no existe (RN-03)."""
    validar_paginacion(limit, offset)
    cliente = await session.get(Cliente, cliente_id)
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    resultado = await session.exec(
        carga_completa_ventas(
            select(Venta)
            .where(Venta.cliente_id == cliente_id)
            .order_by(Venta.id)
            .limit(limit)
            .offset(offset)
        )
    )
    return [venta_a_read(venta) for venta in resultado.all()]
