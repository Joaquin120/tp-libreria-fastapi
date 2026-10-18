"""DTOs del módulo de autores (Ejercicios 4 y 5)."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class AutorCreate(BaseModel):
    """Alta de autor: sin `id`."""

    nombre: str = Field(min_length=1, max_length=150)
    nacionalidad: str = Field(min_length=1, max_length=100)


class AutorUpdate(BaseModel):
    """Actualización parcial: todos los campos opcionales."""

    nombre: str | None = Field(default=None, min_length=1, max_length=150)
    nacionalidad: str | None = Field(default=None, min_length=1, max_length=100)


class AutorRead(BaseModel):
    """Salida de autor."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    nacionalidad: str


class LibroDelAutor(BaseModel):
    """Libro en el que participa el autor, con su `rol` y `orden` (RN: GET /autores/{id}/libros)."""

    id: int
    isbn: str
    titulo: str
    precio: Decimal
    stock: int
    rol: str
    orden: int
