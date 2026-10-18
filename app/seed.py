#!/usr/bin/env python3
"""Estado inicial conocido de la base de datos (Ejercicio de datos semilla).

Limpia TODAS las tablas y recrea un conjunto fijo de datos para poder
ejecutar las pruebas de inmediato:

- Editoriales: Emecé Editores, Editorial Anagrama.
- Géneros: Novela, Cuento.
- Autores: Julio Cortázar, Adolfo Bioy Casares, Jorge Luis Borges.
- Libros: "Rayuela" ($25000.00), "Respiración artificial" ($27000.00) y
  "Ficciones", con sus autorías (rol y orden).
- Clientes: Tomás Ríos (sin perfil) y María Gómez (con perfil).
- Una venta de ejemplo con dos renglones y total calculado en el servidor.

Uso (desde la raíz del proyecto, con el .env configurado):

    python -m app.seed
    ./app/seed.py

Requiere que el esquema ya exista: `alembic upgrade head`.
"""

import asyncio
import sys
from decimal import Decimal
from pathlib import Path

from sqlalchemy import text
from sqlmodel import SQLModel

# Permite ejecutarlo como ./app/seed.py desde cualquier directorio.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.models  # noqa: F401,E402  (centralizador: registra todas las tablas)
from app.core.database import create_db_engine, create_session_factory  # noqa: E402


async def seed() -> None:
    """Limpia las tablas y deja el estado inicial conocido."""
    # La URL llega por entorno/.env (nunca está cableada en el código).
    from app.core.config import get_settings

    settings = get_settings()
    engine = create_db_engine(settings.database_url, echo=False)
    factory = create_session_factory(engine)

    from app.modules.autores.models import Autor
    from app.modules.clientes.models import Cliente, PerfilCliente
    from app.modules.editoriales.models import Editorial
    from app.modules.generos.models import Genero
    from app.modules.libros.models import Libro, LibroAutor
    from app.modules.ventas.models import RenglonVenta, Venta

    async with factory() as session:
        # --- Limpieza total (estado inicial conocido) ---
        # Los nombres de tablas provienen de SQLModel.metadata (no de input
        # externo): RESTART IDENTITY reinicia las secuencias para que los ids
        # sean siempre 1, 2, 3... y los casos de prueba (ej. /clientes/1) sean
        # reproducibles.
        tablas = ", ".join(tabla.name for tabla in SQLModel.metadata.sorted_tables)
        await session.exec(text(f"TRUNCATE {tablas} RESTART IDENTITY CASCADE"))
        await session.commit()

        # --- Catálogo base ---
        emece = Editorial(nombre="Emecé Editores", pais="Argentina")
        anagrama = Editorial(nombre="Editorial Anagrama", pais="España")
        novela = Genero(nombre="Novela")
        cuento = Genero(nombre="Cuento")
        cortazar = Autor(nombre="Julio Cortázar", nacionalidad="Argentina")
        bioy = Autor(nombre="Adolfo Bioy Casares", nacionalidad="Argentina")
        borges = Autor(nombre="Jorge Luis Borges", nacionalidad="Argentina")
        session.add_all([emece, anagrama, novela, cuento, cortazar, bioy, borges])
        await session.flush()  # asigna ids para las FK siguientes

        # --- Libros con sus autorías ---
        rayuela = Libro(
            isbn="978-84-376-0494-7",
            titulo="Rayuela",
            precio=Decimal("25000.00"),
            stock=10,
            editorial_id=emece.id,
            genero_id=novela.id,
        )
        rayuela.autorias = [LibroAutor(autor_id=cortazar.id, rol="autor", orden=1)]

        respiracion = Libro(
            isbn="978-987-1138-89-0",
            titulo="Respiración artificial",
            precio=Decimal("27000.00"),
            stock=5,
            editorial_id=anagrama.id,
            genero_id=novela.id,
        )
        respiracion.autorias = [LibroAutor(autor_id=bioy.id, rol="autor", orden=1)]

        ficciones = Libro(
            isbn="978-84-204-1111-1",
            titulo="Ficciones",
            precio=Decimal("18500.00"),
            stock=8,
            editorial_id=emece.id,
            genero_id=cuento.id,
        )
        ficciones.autorias = [LibroAutor(autor_id=borges.id, rol="autor", orden=1)]

        # --- Clientes ---
        tomas = Cliente(nombre="Tomás Ríos", email="tomas.rios@correo.com")
        maria = Cliente(nombre="María Gómez", email="maria.gomez@correo.com")
        perfil_maria = PerfilCliente(
            cliente_id=None,  # se asigna tras el flush del cliente
            telefono="+54 11 5555-1234",
            direccion="Av. Corrientes 1234, CABA",
        )
        maria.perfil = perfil_maria
        session.add_all([rayuela, respiracion, ficciones, tomas, maria])
        await session.flush()

        # --- Venta de ejemplo (precios y total calculados en el servidor) ---
        precio_rayuela = rayuela.precio
        precio_ficciones = ficciones.precio
        venta = Venta(
            cliente_id=tomas.id,
            total=Decimal("62000.00"),  # 1 * 25000.00 + 2 * 18500.00
        )
        venta.renglones = [
            RenglonVenta(
                libro_id=rayuela.id, cantidad=1, precio_unitario=precio_rayuela
            ),
            RenglonVenta(
                libro_id=ficciones.id, cantidad=2, precio_unitario=precio_ficciones
            ),
        ]
        session.add(venta)

        await session.commit()

        print("Seed aplicado correctamente:")
        print(f"  editoriales: {emece.id} {emece.nombre}, {anagrama.id} {anagrama.nombre}")
        print(f"  géneros:     {novela.id} {novela.nombre}, {cuento.id} {cuento.nombre}")
        print(f"  autores:     {cortazar.id} Cortázar, {bioy.id} Bioy Casares, {borges.id} Borges")
        print(f"  libros:      {rayuela.id} Rayuela (25000.00), "
              f"{respiracion.id} Respiración artificial (27000.00), "
              f"{ficciones.id} Ficciones (18500.00)")
        print(f"  clientes:    {tomas.id} Tomás Ríos, {maria.id} María Gómez (con perfil)")
        print(f"  venta:       #{venta.id} de {venta.cliente_id} total {venta.total}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
