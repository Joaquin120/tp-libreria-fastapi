"""Modelo de la tabla `genero`."""

from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.libros.models import Libro


class Genero(SQLModel, table=True):
    __tablename__ = "genero"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=100, unique=True)

    # 1 a N (opcional): un género agrupa muchos libros.
    libros: list["Libro"] = Relationship(back_populates="genero")
