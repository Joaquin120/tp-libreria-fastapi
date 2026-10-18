"""DTOs del módulo de ventas (Ejercicios 4 y 5).

Reglas clave (RN-04, RN-05, RN-06, RN-07):
- `VentaCreate` sólo recibe `cliente_id` y `renglones` con `libro_id` +
  `cantidad`. NO viajan `precio_unitario`, `total` ni `fecha`: esos valores
  los calcula el servidor.
- RN-05: la venta debe tener al menos 1 renglón y sin `libro_id` repetidos
  (validado con `@field_validator`; el error de Pydantic se traduce en 422).
- `VentaRead` devuelve `cliente` (id, nombre, email) y `renglones` con
  `titulo`, `precio_unitario` y `subtotal` (cantidad * precio_unitario).
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.clientes.schemas import ClienteResumen


class RenglonVentaCreate(BaseModel):
    """Renglon de entrada: SIN `precio_unitario` (lo calcula el servidor)."""

    libro_id: int
    cantidad: int = Field(gt=0, description="La cantidad debe ser mayor a 0")


class VentaCreate(BaseModel):
    """Alta de venta: sin `id`, sin `total` y sin `fecha` (los calcula el servidor)."""

    cliente_id: int
    renglones: list[RenglonVentaCreate]

    @field_validator("renglones")
    @classmethod
    def _validar_renglones(cls, renglones: list[RenglonVentaCreate]) -> list[RenglonVentaCreate]:
        # RN-05: al menos un renglón por venta.
        if not renglones:
            raise ValueError("La venta debe tener al menos un renglón")
        # RN-05: un mismo libro no puede repetirse dentro de una misma venta.
        vistos: set[int] = set()
        for renglon in renglones:
            if renglon.libro_id in vistos:
                raise ValueError(
                    "El mismo libro no puede repetirse en una venta (libro_id duplicado)"
                )
            vistos.add(renglon.libro_id)
        return renglones


class RenglonVentaRead(BaseModel):
    """Renglon de salida con el subtotal calculado en el servidor."""

    libro_id: int
    titulo: str
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal


class VentaRead(BaseModel):
    """Salida de venta con cliente y renglones ya resueltos (carga anticipada)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    fecha: datetime
    total: Decimal
    cliente: ClienteResumen
    renglones: list[RenglonVentaRead]
