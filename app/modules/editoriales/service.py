"""Lógica de negocio del módulo de editoriales (Ejercicios 4 y 5).

Sin consultas previas de unicidad: se inserta directo y el `IntegrityError`
por el UNIQUE de `nombre` se traduce en 409 (RN-01, RN-12).
"""

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.core.pagination import validar_paginacion
from app.modules.editoriales.models import Editorial
from app.modules.editoriales.schemas import EditorialCreate, EditorialRead, EditorialUpdate
from app.modules.libros.models import Libro
from app.modules.libros.schemas import LibroRead
from app.modules.libros.service import carga_completa_libros, libro_a_read


async def crear_editorial(session: AsyncSession, datos: EditorialCreate) -> EditorialRead:
    """Alta de editorial. Si `nombre` ya existe -> 409 (delegado en la BD)."""
    editorial = Editorial.model_validate(datos)
    session.add(editorial)
    try:
        await session.commit()
    except IntegrityError:
        # RN-12: no se expone el error crudo de PostgreSQL, sólo mensaje propio.
        await session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Ya existe una editorial con ese nombre",
        )
    await session.refresh(editorial)
    return EditorialRead.model_validate(editorial)


async def listar_editoriales(
    session: AsyncSession,
    limit: int = 20,
    offset: int = 0,
) -> list[EditorialRead]:
    """Listado paginado (RN-10). Editorial no tiene relaciones de salida."""
    validar_paginacion(limit, offset)
    resultado = await session.exec(
        select(Editorial).order_by(Editorial.id).limit(limit).offset(offset)
    )
    return [EditorialRead.model_validate(e) for e in resultado.all()]


async def obtener_editorial(session: AsyncSession, editorial_id: int) -> EditorialRead:
    """Detalle por id; 404 si no existe."""
    editorial = await session.get(Editorial, editorial_id)
    if editorial is None:
        raise HTTPException(status_code=404, detail="Editorial no encontrada")
    return EditorialRead.model_validate(editorial)


async def actualizar_editorial(
    session: AsyncSession,
    editorial_id: int,
    datos: EditorialUpdate,
) -> EditorialRead:
    """Actualización parcial con `exclude_unset`; nombre repetido -> 409."""
    editorial = await session.get(Editorial, editorial_id)
    if editorial is None:
        raise HTTPException(status_code=404, detail="Editorial no encontrada")

    campos = datos.model_dump(exclude_unset=True)
    for nombre, valor in campos.items():
        setattr(editorial, nombre, valor)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Ya existe una editorial con ese nombre",
        )
    await session.refresh(editorial)
    return EditorialRead.model_validate(editorial)


async def eliminar_editorial(session: AsyncSession, editorial_id: int) -> None:
    """Baja; si tiene libros asociados la BD rechaza por FK -> 409."""
    editorial = await session.get(Editorial, editorial_id)
    if editorial is None:
        raise HTTPException(status_code=404, detail="Editorial no encontrada")

    await session.delete(editorial)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=409,
            detail="No se puede eliminar la editorial porque tiene libros asociados",
        )


async def listar_libros_editorial(
    session: AsyncSession,
    editorial_id: int,
    limit: int = 20,
    offset: int = 0,
) -> list[LibroRead]:
    """Libros de una editorial; 404 si la editorial no existe (RN-03, sin N+1)."""
    validar_paginacion(limit, offset)
    editorial = await session.get(Editorial, editorial_id)
    if editorial is None:
        raise HTTPException(status_code=404, detail="Editorial no encontrada")

    resultado = await session.exec(
        carga_completa_libros(
            select(Libro)
            .where(Libro.editorial_id == editorial_id)
            .order_by(Libro.id)
            .limit(limit)
            .offset(offset)
        )
    )
    return [libro_a_read(libro) for libro in resultado.all()]
