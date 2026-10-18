"""Lógica de negocio del módulo de autores (Ejercicios 4 y 5).

`autor` no tiene columnas únicas: el alta nunca puede chocar por unicidad,
pero la baja sí puede chocar por FK (`libro_autor`) -> 409.
"""

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.core.pagination import validar_paginacion
from app.modules.autores.models import Autor
from app.modules.autores.schemas import AutorCreate, AutorRead, AutorUpdate, LibroDelAutor
from app.modules.libros.models import LibroAutor


async def crear_autor(session: AsyncSession, datos: AutorCreate) -> AutorRead:
    """Alta de autor: insert directo, sin consultas previas."""
    autor = Autor.model_validate(datos)
    session.add(autor)
    try:
        await session.commit()
    except IntegrityError:
        # RN-12: mensaje propio por si la BD rechaza la operación.
        await session.rollback()
        raise HTTPException(
            status_code=409,
            detail="No se pudo crear el autor: los datos ya existen o son inválidos",
        )
    await session.refresh(autor)
    return AutorRead.model_validate(autor)


async def listar_autores(
    session: AsyncSession,
    limit: int = 20,
    offset: int = 0,
) -> list[AutorRead]:
    """Listado paginado (RN-10)."""
    validar_paginacion(limit, offset)
    resultado = await session.exec(
        select(Autor).order_by(Autor.id).limit(limit).offset(offset)
    )
    return [AutorRead.model_validate(a) for a in resultado.all()]


async def obtener_autor(session: AsyncSession, autor_id: int) -> AutorRead:
    """Detalle por id; 404 si no existe."""
    autor = await session.get(Autor, autor_id)
    if autor is None:
        raise HTTPException(status_code=404, detail="Autor no encontrado")
    return AutorRead.model_validate(autor)


async def actualizar_autor(
    session: AsyncSession,
    autor_id: int,
    datos: AutorUpdate,
) -> AutorRead:
    """Actualización parcial con `exclude_unset`."""
    autor = await session.get(Autor, autor_id)
    if autor is None:
        raise HTTPException(status_code=404, detail="Autor no encontrado")

    campos = datos.model_dump(exclude_unset=True)
    for nombre, valor in campos.items():
        setattr(autor, nombre, valor)

    await session.commit()
    await session.refresh(autor)
    return AutorRead.model_validate(autor)


async def eliminar_autor(session: AsyncSession, autor_id: int) -> None:
    """Baja; si el autor tiene libros asociados la BD rechaza por FK -> 409."""
    autor = await session.get(Autor, autor_id)
    if autor is None:
        raise HTTPException(status_code=404, detail="Autor no encontrado")

    await session.delete(autor)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=409,
            detail="No se puede eliminar el autor porque tiene libros asociados",
        )


async def listar_libros_del_autor(
    session: AsyncSession,
    autor_id: int,
    limit: int = 20,
    offset: int = 0,
) -> list[LibroDelAutor]:
    """Libros del autor con su `rol` y `orden` (RN-03, sin N+1).

    404 si el autor no existe; cada autoría trae su libro con `joinedload`
    en UNA sola consulta.
    """
    validar_paginacion(limit, offset)
    autor = await session.get(Autor, autor_id)
    if autor is None:
        raise HTTPException(status_code=404, detail="Autor no encontrado")

    resultado = await session.exec(
        select(LibroAutor)
        .where(LibroAutor.autor_id == autor_id)
        .options(joinedload(LibroAutor.libro))
        .order_by(LibroAutor.orden, LibroAutor.libro_id)
        .limit(limit)
        .offset(offset)
    )
    return [
        LibroDelAutor(
            id=autoria.libro.id,
            isbn=autoria.libro.isbn,
            titulo=autoria.libro.titulo,
            precio=autoria.libro.precio,
            stock=autoria.libro.stock,
            rol=autoria.rol,
            orden=autoria.orden,
        )
        for autoria in resultado.all()
    ]
