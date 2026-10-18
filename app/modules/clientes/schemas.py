"""DTOs del módulo de clientes (Ejercicios 4 y 5).

Reglas clave:
- `ClienteCreate` NO lleva `id` (RN-02: `email` único, se valida en BD).
- `PerfilClienteCreate` NO lleva `id` ni `cliente_id` (va en la URL).
- `Cliente.perfil` es una relación 1 a 1: en la salida es objeto o `None`,
  nunca una lista.
"""

from pydantic import BaseModel, ConfigDict, Field


class ClienteCreate(BaseModel):
    """Alta de cliente: sin `id`."""

    nombre: str = Field(min_length=1, max_length=150)
    email: str = Field(min_length=3, max_length=250)


class ClienteUpdate(BaseModel):
    """Actualización parcial: todos los campos opcionales."""

    nombre: str | None = Field(default=None, min_length=1, max_length=150)
    email: str | None = Field(default=None, min_length=3, max_length=250)


class PerfilClienteCreate(BaseModel):
    """Alta de perfil (el `cliente_id` llega por la URL)."""

    telefono: str = Field(min_length=1, max_length=30)
    direccion: str = Field(min_length=1, max_length=250)


class PerfilClienteUpdate(BaseModel):
    """Actualización parcial del perfil: todos los campos opcionales."""

    telefono: str | None = Field(default=None, min_length=1, max_length=30)
    direccion: str | None = Field(default=None, min_length=1, max_length=250)


class PerfilClienteRead(BaseModel):
    """Salida de perfil."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    cliente_id: int
    telefono: str
    direccion: str


class ClienteResumen(BaseModel):
    """Resumen de cliente tal como aparece dentro de una `VentaRead`."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    email: str


class ClienteRead(BaseModel):
    """Salida de cliente con su perfil (objeto o None, jamás lista)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    email: str
    perfil: PerfilClienteRead | None = None
