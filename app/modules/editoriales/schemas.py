"""DTOs del módulo de editoriales (Ejercicios 4 y 5)."""

from pydantic import BaseModel, ConfigDict, Field


class EditorialCreate(BaseModel):
    """Alta de editorial: sin `id` (lo asigna la base de datos)."""

    nombre: str = Field(min_length=1, max_length=150)
    pais: str = Field(min_length=1, max_length=100)


class EditorialUpdate(BaseModel):
    """Actualización parcial: todos los campos opcionales (RN: exclude_unset)."""

    nombre: str | None = Field(default=None, min_length=1, max_length=150)
    pais: str | None = Field(default=None, min_length=1, max_length=100)


class EditorialRead(BaseModel):
    """Salida de editorial."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    pais: str
