"""Paginación compartida por todos los listados (RN-10)."""

from fastapi import HTTPException


def validar_paginacion(limit: int, offset: int) -> None:
    """Valida los parámetros de paginación de los listados.

    RN-10: `limit` entre 1 y 100 (por defecto 20) y `offset >= 0` (por defecto 0).
    Si el router no lo validó con `Query(ge=1, le=100)`, esta validación de
    respaldo devuelve 422 en lugar de un 500 por valores fuera de rango.
    """
    if not 1 <= limit <= 100:
        raise HTTPException(
            status_code=422,
            detail="El parámetro 'limit' debe estar entre 1 y 100",
        )
    if offset < 0:
        raise HTTPException(
            status_code=422,
            detail="El parámetro 'offset' no puede ser negativo",
        )
