"""Modelos de las tablas `cliente` y `perfil_cliente` (relación 1 a 1)."""

from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.ventas.models import Venta


class Cliente(SQLModel, table=True):
    __tablename__ = "cliente"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=150)
    email: str = Field(max_length=250, unique=True)

    # 1 a 1: `uselist=False` garantiza objeto o None, nunca lista.
    # Nota: `Optional["Clase"]` en lugar de `"Clase | None"` porque SQLModel
    # resuelve unions con ForwardRef pero no strings literales de PEP 604.
    perfil: Optional["PerfilCliente"] = Relationship(
        back_populates="cliente",
        sa_relationship_kwargs={"uselist": False},
    )
    ventas: list["Venta"] = Relationship(back_populates="cliente")


class PerfilCliente(SQLModel, table=True):
    __tablename__ = "perfil_cliente"

    id: int | None = Field(default=None, primary_key=True)
    # A la vez única (1 a 1) e indexada (RN de FK).
    cliente_id: int = Field(foreign_key="cliente.id", unique=True, index=True)
    telefono: str = Field(max_length=30)
    direccion: str = Field(max_length=250)

    cliente: Cliente = Relationship(back_populates="perfil")
