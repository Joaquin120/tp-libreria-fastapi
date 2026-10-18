from contextlib import asynccontextmanager
import logging
from typing import AsyncIterator

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.database import create_db_engine, create_session_factory
from app.modules.autores.router import router as autores_router
from app.modules.clientes.router import router as clientes_router
from app.modules.editoriales.router import router as editoriales_router
from app.modules.generos.router import router as generos_router
from app.modules.health.router import router as health_router
from app.modules.libros.router import router as libros_router
from app.modules.ventas.router import router as ventas_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Ciclo de vida: crea motor y fábrica de sesiones al arrancar; dispose al apagar.

    No se usa `SQLModel.metadata.create_all` en ninguna parte: el esquema se
    gestiona exclusivamente con Alembic (asincrónico).
    """
    # Habilita los logs de INFO en consola (ej. el comprobante de la venta,
    # Ejercicio 7) sin pisar la configuración de logging de uvicorn.
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    engine = create_db_engine(settings.database_url, settings.db_echo)
    app.state.engine = engine
    app.state.session_factory = create_session_factory(engine)
    try:
        yield
    finally:
        await engine.dispose()


app = FastAPI(
    title="API Librería",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(editoriales_router)
app.include_router(generos_router)
app.include_router(autores_router)
app.include_router(libros_router)
app.include_router(clientes_router)
app.include_router(ventas_router)


@app.get("/", status_code=200, tags=["root"])
async def root() -> dict[str, str]:
    return {"mensaje": "API Librería - Ejercicio 1"}
