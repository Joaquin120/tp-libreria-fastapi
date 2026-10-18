"""DTOs del módulo de géneros (Ejercicios 4 y 5)."""

from pydantic import BaseModel, ConfigDict, Field


class GeneroCreate(BaseModel):
    """Alta de género: sin `id`."""

    nombre: str = Field(min_length=1, max_length=100)


class GeneroUpdate(BaseModel):
    """Actualización parcial: todos los campos opcionales."""

    nombre: str | None = Field(default=None, min_length=1, max_length=100)


class GeneroRead(BaseModel):
    """Salida de género."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
