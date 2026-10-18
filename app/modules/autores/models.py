"""Modelo de la tabla `autor`."""

from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.libros.models import LibroAutor


class Autor(SQLModel, table=True):
    __tablename__ = "autor"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=150)
    nacionalidad: str = Field(max_length=100)

    # N a N con `libro` a través de la tabla asociativa `libro_autor`.
    autorias: list["LibroAutor"] = Relationship(back_populates="autor")
