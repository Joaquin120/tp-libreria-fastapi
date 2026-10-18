"""Lógica de negocio del módulo de libros (Ejercicios 4, 5 y 6).

Reglas clave:
- ALTA SIN `if` PREVIOS (RN-01, RN-12): se inserta `Libro` + sus `LibroAutor`
  directamente; cualquier `IntegrityError` (ISBN repetido, FK inexistente) se
  traduce en 409 con mensaje propio, sin exponer datos internos de PostgreSQL.
- SIN N+1 (RN-03): todas las lecturas usan `joinedload` (relaciones a uno) y
  `selectinload` (colecciones) para responder en un número fijo de consultas.
"""

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from sqlmodel import select

from app.core.pagination import validar_paginacion
from app.modules.libros.models import Libro, LibroAutor
from app.modules.libros.schemas import (
    AutorResumen,
    EditorialRead,
    GeneroRead,
    LibroAutorRead,
    LibroCreate,
    LibroRead,
    LibroUpdate,
)


def carga_completa_libros(stmt):
    """Opciones de carga anticipada compartidas por TODAS las lecturas de libros.

    - `joinedload` para relaciones a uno: editorial y genero.
    - `selectinload` para la colección `autorias`, encadenado con
      `joinedload(LibroAutor.autor)` para traer cada autor en la misma consulta
      (sin esto, armar el DTO dispararía N+1 consultas -> lazy loading).
    """
    return stmt.options(
        joinedload(Libro.editorial),
        joinedload(Libro.genero),
        selectinload(Libro.autorias).joinedload(LibroAutor.autor),
    )


def libro_a_read(libro: Libro) -> LibroRead:
    """Construye el DTO de salida a partir de un libro ya precargado."""
    return LibroRead(
        id=libro.id,
        isbn=libro.isbn,
        titulo=libro.titulo,
        precio=libro.precio,
        stock=libro.stock,
        editorial_id=libro.editorial_id,
        genero_id=libro.genero_id,
        editorial=EditorialRead.model_validate(libro.editorial),
        genero=(
            GeneroRead.model_validate(libro.genero)
            if libro.genero is not None
            else None
        ),
        autores=[
            LibroAutorRead(
                autor_id=autoria.autor_id,
                rol=autoria.rol,
                orden=autoria.orden,
                autor=AutorResumen.model_validate(autoria.autor),
            )
            for autoria in sorted(libro.autorias, key=lambda a: a.orden)
        ],
    )


async def _recargar_libro(session: AsyncSession, libro_id: int) -> LibroRead:
    """Recarga el libro con toda la carga anticipada (post commit) para el DTO."""
    resultado = await session.exec(
        carga_completa_libros(select(Libro).where(Libro.id == libro_id))
    )
    libro = resultado.one()
    return libro_a_read(libro)


async def crear_libro(session: AsyncSession, datos: LibroCreate) -> LibroRead:
    """Alta de libro con sus autorías en un solo commit.

    NO se consulta antes si el ISBN o las FK existen: se inserta directo y la
    base de datos delega la decisión. Cualquier violación (ISBN único,
    editorial_id/genero_id/autor_id inexistente) revienta como IntegrityError
    y se traduce en 409 sin exponer el error crudo (RN-12).
    """
    libro = Libro(
        isbn=datos.isbn,
        titulo=datos.titulo,
        precio=datos.precio,
        stock=datos.stock,
        editorial_id=datos.editorial_id,
        genero_id=datos.genero_id,
    )
    # Las autorías se crean en memoria y viajan en el mismo INSERT (cascade).
    libro.autorias = [
        LibroAutor(autor_id=autoria.autor_id, rol=autoria.rol, orden=autoria.orden)
        for autoria in datos.autores
    ]
    session.add(libro)
    try:
        await session.commit()
    except IntegrityError:
        # RN-01/RN-12: mensaje propio y amigable; jamás el texto de Postgres.
        await session.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                "No se pudo crear el libro: el ISBN debe ser único y la "
                "editorial, el género y los autores deben existir"
            ),
        )
    return await _recargar_libro(session, libro.id)


async def listar_libros(
    session: AsyncSession,
    limit: int = 20,
    offset: int = 0,
    titulo: str | None = None,
    genero_id: int | None = None,
) -> list[LibroRead]:
    """Listado paginado con filtros opcionales (RN-10, RN-11).

    - `titulo`: filtro insensible a mayúsculas con `ilike` y parámetro ligado.
    - `genero_id`: filtro exacto opcional.
    - Carga anticipada en UNA sola consulta (sin N+1).
    """
    validar_paginacion(limit, offset)
    stmt = carga_completa_libros(select(Libro))
    if titulo:
        # Parámetro ligado por SQLAlchemy: jamás se concatena SQL (RN-11).
        stmt = stmt.where(Libro.titulo.ilike(f"%{titulo}%"))
    if genero_id is not None:
        stmt = stmt.where(Libro.genero_id == genero_id)
    stmt = stmt.order_by(Libro.id).limit(limit).offset(offset)
    resultado = await session.exec(stmt)
    return [libro_a_read(libro) for libro in resultado.all()]


async def obtener_libro(session: AsyncSession, libro_id: int) -> LibroRead:
    """Detalle por id con carga anticipada; 404 si no existe."""
    resultado = await session.exec(
        carga_completa_libros(select(Libro).where(Libro.id == libro_id))
    )
    libro = resultado.one_or_none()
    if libro is None:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    return libro_a_read(libro)


async def actualizar_libro(
    session: AsyncSession,
    libro_id: int,
    datos: LibroUpdate,
) -> LibroRead:
    """Actualización parcial con `exclude_unset`; conflictos -> 409."""
    libro = await session.get(Libro, libro_id)
    if libro is None:
        raise HTTPException(status_code=404, detail="Libro no encontrado")

    campos = datos.model_dump(exclude_unset=True)
    for nombre, valor in campos.items():
        setattr(libro, nombre, valor)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                "No se pudo actualizar el libro: el ISBN debe ser único y la "
                "editorial y el género deben existir"
            ),
        )
    # Recarga con carga anticipada para responder con el DTO completo.
    return await _recargar_libro(session, libro.id)


async def eliminar_libro(session: AsyncSession, libro_id: int) -> None:
    """Baja; si el libro tiene renglones de venta la BD rechaza por FK -> 409."""
    libro = await session.get(Libro, libro_id)
    if libro is None:
        raise HTTPException(status_code=404, detail="Libro no encontrado")

    await session.delete(libro)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=409,
            detail="No se puede eliminar el libro porque tiene ventas asociadas",
        )
