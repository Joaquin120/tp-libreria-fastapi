"""Lógica de negocio del módulo de géneros (Ejercicios 4 y 5).

Sin consultas previas de unicidad: se inserta directo y el `IntegrityError`
por el UNIQUE de `nombre` se traduce en 409 (RN-01, RN-12).
"""

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.core.pagination import validar_paginacion
from app.modules.generos.models import Genero
from app.modules.generos.schemas import GeneroCreate, GeneroRead, GeneroUpdate
from app.modules.libros.models import Libro
from app.modules.libros.schemas import LibroRead
from app.modules.libros.service import carga_completa_libros, libro_a_read


async def crear_genero(session: AsyncSession, datos: GeneroCreate) -> GeneroRead:
    """Alta de género. Si `nombre` ya existe -> 409 (delegado en la BD)."""
    genero = Genero.model_validate(datos)
    session.add(genero)
    try:
        await session.commit()
    except IntegrityError:
        # RN-12: mensaje propio, sin exponer constraints ni tablas.
        await session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Ya existe un género con ese nombre",
        )
    await session.refresh(genero)
    return GeneroRead.model_validate(genero)


async def listar_generos(
    session: AsyncSession,
    limit: int = 20,
    offset: int = 0,
) -> list[GeneroRead]:
    """Listado paginado (RN-10). Género no tiene relaciones de salida."""
    validar_paginacion(limit, offset)
    resultado = await session.exec(
        select(Genero).order_by(Genero.id).limit(limit).offset(offset)
    )
    return [GeneroRead.model_validate(g) for g in resultado.all()]


async def obtener_genero(session: AsyncSession, genero_id: int) -> GeneroRead:
    """Detalle por id; 404 si no existe."""
    genero = await session.get(Genero, genero_id)
    if genero is None:
        raise HTTPException(status_code=404, detail="Género no encontrado")
    return GeneroRead.model_validate(genero)


async def actualizar_genero(
    session: AsyncSession,
    genero_id: int,
    datos: GeneroUpdate,
) -> GeneroRead:
    """Actualización parcial con `exclude_unset`; nombre repetido -> 409."""
    genero = await session.get(Genero, genero_id)
    if genero is None:
        raise HTTPException(status_code=404, detail="Género no encontrado")

    campos = datos.model_dump(exclude_unset=True)
    for nombre, valor in campos.items():
        setattr(genero, nombre, valor)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Ya existe un género con ese nombre",
        )
    await session.refresh(genero)
    return GeneroRead.model_validate(genero)


async def eliminar_genero(session: AsyncSession, genero_id: int) -> None:
    """Baja; si tiene libros asociados la BD rechaza por FK -> 409."""
    genero = await session.get(Genero, genero_id)
    if genero is None:
        raise HTTPException(status_code=404, detail="Género no encontrado")

    await session.delete(genero)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=409,
            detail="No se puede eliminar el género porque tiene libros asociados",
        )


async def listar_libros_genero(
    session: AsyncSession,
    genero_id: int,
    limit: int = 20,
    offset: int = 0,
) -> list[LibroRead]:
    """Libros de un género; 404 si el género no existe (RN-03, sin N+1)."""
    validar_paginacion(limit, offset)
    genero = await session.get(Genero, genero_id)
    if genero is None:
        raise HTTPException(status_code=404, detail="Género no encontrado")

    resultado = await session.exec(
        carga_completa_libros(
            select(Libro)
            .where(Libro.genero_id == genero_id)
            .order_by(Libro.id)
            .limit(limit)
            .offset(offset)
        )
    )
    return [libro_a_read(libro) for libro in resultado.all()]
