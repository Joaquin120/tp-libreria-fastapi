"""Lógica de negocio del módulo de ventas (Ejercicios 4, 5, 6 y 7).

Reglas clave:
- RN-04: el precio de cada renglón es el precio ACTUAL del `Libro`, copiado
  en el servidor; el cliente nunca envía precios.
- RN-06: `total` calculado en el servidor como suma de cantidad * precio.
- RN-05: los renglones se validan en el DTO (>= 1 y sin libros repetidos).
- RN-12: un `cliente_id` o `libro_id` inexistente revienta como IntegrityError
  en el INSERT (FK) -> 409, sin consultas previas de existencia.
- Sin N+1 (RN-03): `Venta.cliente` con `joinedload` y `Venta.renglones` con
  `selectinload` encadenado a `RenglonVenta.libro`.
- Ejercicio 7: `BackgroundTasks` agenda `enviar_comprobante_venta` (asincrónica,
  con `asyncio.sleep` y log) para ejecutarse DESPUÉS de responder.
"""

import asyncio
import logging
from decimal import Decimal

from fastapi import BackgroundTasks, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from sqlmodel import select

from app.core.pagination import validar_paginacion
from app.modules.clientes.schemas import ClienteResumen
from app.modules.libros.models import Libro
from app.modules.ventas.models import RenglonVenta, Venta
from app.modules.ventas.schemas import (
    RenglonVentaCreate,
    RenglonVentaRead,
    VentaCreate,
    VentaRead,
)


async def enviar_comprobante_venta(venta_id: int, email_cliente: str) -> None:
    """Simula el envío del comprobante de venta por email (Ejercicio 7).

    Se ejecuta como BackgroundTask DESPUÉS de que FastAPI responde al cliente:
    espera 0.5 s (asincrónico, sin bloquear el event loop) y registra el
    envío en el log.
    """
    await asyncio.sleep(0.5)
    logging.info(
        "Comprobante de la venta #%s enviado a %s",
        venta_id,
        email_cliente,
    )


def carga_completa_ventas(stmt):
    """Carga anticipada compartida por TODAS las lecturas de ventas (RN-03)."""
    return stmt.options(
        joinedload(Venta.cliente),
        selectinload(Venta.renglones).joinedload(RenglonVenta.libro),
    )


def venta_a_read(venta: Venta) -> VentaRead:
    """DTO de venta con cliente y renglones ya resueltos (sin lazy loading)."""
    return VentaRead(
        id=venta.id,
        fecha=venta.fecha,
        total=venta.total,
        cliente=ClienteResumen.model_validate(venta.cliente),
        renglones=[
            RenglonVentaRead(
                libro_id=renglon.libro_id,
                titulo=renglon.libro.titulo,
                cantidad=renglon.cantidad,
                precio_unitario=renglon.precio_unitario,
                # Subtotal calculado en el servidor con Decimal (nunca float).
                subtotal=renglon.cantidad * renglon.precio_unitario,
            )
            for renglon in sorted(venta.renglones, key=lambda r: r.id)
        ],
    )


async def _recargar_venta(session: AsyncSession, venta_id: int) -> VentaRead:
    """Recarga la venta con carga anticipada tras el commit, para el DTO."""
    resultado = await session.exec(
        carga_completa_ventas(select(Venta).where(Venta.id == venta_id))
    )
    return venta_a_read(resultado.one())


async def crear_venta(
    session: AsyncSession,
    datos: VentaCreate,
    background_tasks: BackgroundTasks,
) -> VentaRead:
    """Alta de venta con sus renglones (RN-04, RN-06, RN-07).

    1. Trae los libros involucrados con una sola consulta y copia su precio
       actual en cada renglón (RN-04).
    2. Si algún `libro_id` no existe -> 409 (caso C-05).
    3. Calcula el `total` en el servidor (RN-06); jamás llega del cliente.
    4. Inserta `Venta` + renglones por composición en UN commit; si el
       `cliente_id` es inexistente la FK revienta -> IntegrityError -> 409
       (se delega en la BD, sin `if` previos; RN-12).
    5. Agenda el comprobante en background (Ejercicio 7).
    """
    libros_ids = {renglon.libro_id for renglon in datos.renglones}
    resultado = await session.exec(select(Libro).where(Libro.id.in_(libros_ids)))
    libros = {libro.id: libro for libro in resultado.all()}

    faltantes = libros_ids - libros.keys()
    if faltantes:
        raise HTTPException(
            status_code=409,
            detail="No se pudo registrar la venta: uno o más libros no existen",
        )

    # RN-04 + RN-06: precios copiados del servidor y total calculado acá.
    venta = Venta(cliente_id=datos.cliente_id, total=Decimal("0.00"))
    total = Decimal("0.00")
    for renglon in datos.renglones:
        libro = libros[renglon.libro_id]
        precio_unitario = libro.precio
        venta.renglones.append(
            RenglonVenta(
                libro_id=renglon.libro_id,
                cantidad=renglon.cantidad,
                precio_unitario=precio_unitario,
            )
        )
        total += renglon.cantidad * precio_unitario
    venta.total = total

    session.add(venta)
    try:
        await session.commit()
    except IntegrityError:
        # RN-12: cliente inexistente (u otra FK) -> mensaje propio, 409.
        await session.rollback()
        raise HTTPException(
            status_code=409,
            detail="No se pudo registrar la venta: el cliente no existe",
        )

    # Recarga con carga anticipada para el DTO en un número fijo de consultas.
    venta_read = await _recargar_venta(session, venta.id)

    # Ejercicio 7: se agenda DESPUÉS de responder (el handler ya devolvió).
    background_tasks.add_task(
        enviar_comprobante_venta,
        venta_read.id,
        venta_read.cliente.email,
    )
    return venta_read


async def listar_ventas(
    session: AsyncSession,
    limit: int = 20,
    offset: int = 0,
) -> list[VentaRead]:
    """Listado paginado (RN-10) con cliente y renglones precargados (RN-03)."""
    validar_paginacion(limit, offset)
    resultado = await session.exec(
        carga_completa_ventas(
            select(Venta).order_by(Venta.id).limit(limit).offset(offset)
        )
    )
    return [venta_a_read(venta) for venta in resultado.all()]


async def obtener_venta(session: AsyncSession, venta_id: int) -> VentaRead:
    """Detalle por id con carga anticipada; 404 si no existe."""
    resultado = await session.exec(
        carga_completa_ventas(select(Venta).where(Venta.id == venta_id))
    )
    venta = resultado.one_or_none()
    if venta is None:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    return venta_a_read(venta)
