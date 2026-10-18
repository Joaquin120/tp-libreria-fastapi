"""Modelos de las tablas `libro` y `libro_autor` (objeto de asociación)."""

from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, Numeric
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.autores.models import Autor
    from app.modules.editoriales.models import Editorial
    from app.modules.generos.models import Genero
    from app.modules.ventas.models import RenglonVenta


class LibroAutor(SQLModel, table=True):
    """Objeto de asociación N a N entre `libro` y `autor` con atributos propios."""

    __tablename__ = "libro_autor"
    __table_args__ = (
        CheckConstraint("orden >= 1", name="ck_libro_autor_orden_positivo"),
        CheckConstraint(
            "rol IN ('autor', 'coautor', 'traductor', 'ilustrador')",
            name="ck_libro_autor_rol_valido",
        ),
    )

    libro_id: int = Field(foreign_key="libro.id", primary_key=True, index=True)
    autor_id: int = Field(foreign_key="autor.id", primary_key=True, index=True)
    rol: str = Field(max_length=20)
    orden: int

    libro: "Libro" = Relationship(back_populates="autorias")
    autor: "Autor" = Relationship(back_populates="autorias")


class Libro(SQLModel, table=True):
    __tablename__ = "libro"
    __table_args__ = (
        CheckConstraint("precio > 0", name="ck_libro_precio_positivo"),
        CheckConstraint("stock >= 0", name="ck_libro_stock_no_negativo"),
    )

    id: int | None = Field(default=None, primary_key=True)
    isbn: str = Field(max_length=17, unique=True)
    titulo: str = Field(max_length=250)
    precio: Decimal = Field(sa_type=Numeric(10, 2))
    stock: int = Field(default=0)

    # Obligatoria: siempre hay una editorial. Indexada (RN de FK).
    editorial_id: int = Field(foreign_key="editorial.id", index=True)
    # Opcional: puede no tener género asignado. Indexada (RN de FK).
    genero_id: int | None = Field(default=None, foreign_key="genero.id", index=True)

    editorial: "Editorial" = Relationship(back_populates="libros")
    genero: Optional["Genero"] = Relationship(back_populates="libros")
    # Composición: al borrar el libro se borran sus autorías.
    autorias: list[LibroAutor] = Relationship(
        back_populates="libro",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    renglones_venta: list["RenglonVenta"] = Relationship(back_populates="libro")
