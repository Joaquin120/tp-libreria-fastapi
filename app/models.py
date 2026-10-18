"""Centralizador de modelos.

Importa todos los modelos de la aplicación para que:

- `SQLModel.metadata` tenga registradas TODAS las tablas (requisito de
  `alembic revision --autogenerate`).
- Todas las clases estén definidas antes de que SQLAlchemy resuelva las
  relaciones con anotaciones forward (`"Libro"`, `"RenglonVenta"`, etc.).

En `alembic/env.py` basta con `import app.models` (o importar este módulo
antes de acceder a `target_metadata`).
"""

from app.modules.autores.models import Autor
from app.modules.clientes.models import Cliente, PerfilCliente
from app.modules.editoriales.models import Editorial
from app.modules.generos.models import Genero
from app.modules.libros.models import Libro, LibroAutor
from app.modules.ventas.models import RenglonVenta, Venta

__all__ = [
    "Autor",
    "Cliente",
    "PerfilCliente",
    "Editorial",
    "Genero",
    "Libro",
    "LibroAutor",
    "Venta",
    "RenglonVenta",
]
