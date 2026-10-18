"""Modelo de la tabla `editorial`."""

from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.libros.models import Libro


class Editorial(SQLModel, table=True):
    __tablename__ = "editorial"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=150, unique=True)
    pais: str = Field(max_length=100)

    # 1 a N: una editorial publica muchos libros.
    libros: list["Libro"] = Relationship(back_populates="editorial")
