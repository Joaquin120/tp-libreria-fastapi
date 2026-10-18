"""DTOs del módulo de libros (Ejercicios 4 y 5).

Reglas clave:
- `LibroCreate` NO lleva `id`.
- `precio > 0` y `stock >= 0` validados a nivel de DTO (FastAPI devuelve 422).
- `autores` (autorías) viaja como lista de objetos con `autor_id`, `rol`
  (Literal de roles válidos) y `orden >= 1`.
- `LibroUpdate` tiene TODOS los campos opcionales (se aplican con
  `model_dump(exclude_unset=True)` en el service).
"""

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.editoriales.schemas import EditorialRead
from app.modules.generos.schemas import GeneroRead

RolLibro = Literal["autor", "coautor", "traductor", "ilustrador"]


class AutorResumen(BaseModel):
    """Resumen de autor tal como aparece dentro de una autoría."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class LibroAutorCreate(BaseModel):
    """Autoría individual dentro de `LibroCreate.autores`."""

    autor_id: int
    rol: RolLibro
    orden: int = Field(ge=1, description="Posición del autor en el libro, >= 1")


class LibroCreate(BaseModel):
    """Alta de libro: sin `id` (lo asigna la base de datos)."""

    isbn: str = Field(min_length=1, max_length=17)
    titulo: str = Field(min_length=1, max_length=250)
    precio: Decimal = Field(gt=0, description="El precio debe ser mayor a 0")
    stock: int = Field(ge=0, description="El stock no puede ser negativo")
    editorial_id: int
    genero_id: int | None = None
    autores: list[LibroAutorCreate] = Field(default_factory=list)


class LibroUpdate(BaseModel):
    """Actualización parcial: todos los campos opcionales (sin autorías)."""

    isbn: str | None = Field(default=None, min_length=1, max_length=17)
    titulo: str | None = Field(default=None, min_length=1, max_length=250)
    precio: Decimal | None = Field(default=None, gt=0)
    stock: int | None = Field(default=None, ge=0)
    editorial_id: int | None = None
    genero_id: int | None = None


class LibroAutorRead(BaseModel):
    """Autoría de salida, con el autor resuelto (carga anticipada)."""

    model_config = ConfigDict(from_attributes=True)

    autor_id: int
    rol: str
    orden: int
    autor: AutorResumen


class LibroRead(BaseModel):
    """Salida de libro con editorial, género y autorías ya resueltos."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    isbn: str
    titulo: str
    precio: Decimal
    stock: int
    editorial_id: int
    genero_id: int | None
    editorial: EditorialRead
    genero: GeneroRead | None
    autores: list[LibroAutorRead]
