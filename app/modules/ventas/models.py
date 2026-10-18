"""Modelos de las tablas `venta` y `renglon_venta`."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Numeric
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.clientes.models import Cliente
    from app.modules.libros.models import Libro


def _utc_now() -> datetime:
    """Fecha/hora actual consciente de la zona horaria (UTC)."""
    return datetime.now(timezone.utc)


class Venta(SQLModel, table=True):
    __tablename__ = "venta"
    __table_args__ = (
        CheckConstraint("total >= 0", name="ck_venta_total_no_negativo"),
    )

    id: int | None = Field(default=None, primary_key=True)
    cliente_id: int = Field(foreign_key="cliente.id", index=True)
    fecha: datetime = Field(default_factory=_utc_now, sa_type=DateTime(timezone=True))
    total: Decimal = Field(sa_type=Numeric(12, 2))

    cliente: "Cliente" = Relationship(back_populates="ventas")
    # Composición: al borrar la venta se borran sus renglones.
    renglones: list["RenglonVenta"] = Relationship(
        back_populates="venta",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class RenglonVenta(SQLModel, table=True):
    __tablename__ = "renglon_venta"
    __table_args__ = (
        CheckConstraint("cantidad > 0", name="ck_renglon_cantidad_positiva"),
        CheckConstraint("precio_unitario > 0", name="ck_renglon_precio_positivo"),
    )

    id: int | None = Field(default=None, primary_key=True)
    venta_id: int = Field(foreign_key="venta.id", index=True)
    libro_id: int = Field(foreign_key="libro.id", index=True)
    cantidad: int
    precio_unitario: Decimal = Field(sa_type=Numeric(10, 2))

    venta: "Venta" = Relationship(back_populates="renglones")
    libro: "Libro" = Relationship(back_populates="renglones_venta")
