# TP Programación III — API RESTful de Librería (100% asincrónica)

API REST asincrónica para una librería (catálogo, clientes y ventas) construida con
**Python 3.12, FastAPI, SQLModel/SQLAlchemy 2.0 (asincrónico), asyncpg, PostgreSQL 16 y Alembic**.

Reglas duras del proyecto:

- Todos los handlers y servicios son `async def`; sin llamadas bloqueantes.
- El esquema se gestiona **solo con Alembic asincrónico** (nunca `create_all`).
- Sin lazy loading ni N+1: `joinedload` para relaciones a uno y `selectinload`
  para colecciones, siempre en la misma consulta.
- Sin consultas `if` previas de existencia/unicidad: se inserta directo y el
  `IntegrityError` se traduce en **409** con mensaje propio (RN-01/RN-12).
- Dinero siempre en `Decimal` / `NUMERIC`; SQL con parámetros ligados (RN-11).

---

## 1. Requisitos

- Python 3.12
- PostgreSQL 16 corriendo y una base vacía creada, por ejemplo:

```bash
createdb libreria_db
```

## 2. Entorno virtual e instalación

```bash
# desde la raíz del proyecto
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Configuración (`.env`)

```bash
cp .env.example .env
```

`.env.example`:

```env
DATABASE_URL=postgresql+asyncpg://usuario:password@localhost:5432/libreria_db
DB_ECHO=False
```

Editá `DATABASE_URL` con tus credenciales. **La URL nunca está cableada en el
código**: `alembic.ini` la deja comentada y `migrations/env.py` la inyecta desde
`settings.DATABASE_URL`.

Para la evidencia del caso C-07 (sección 8) usá `DB_ECHO=True`, que hace que
SQLAlchemy imprima cada consulta en consola.

## 4. Migraciones

```bash
# crear el esquema completo (todas las tablas)
alembic upgrade head

# probar el ciclo inverso (deja la base vacía)
alembic downgrade -1

# volver al esquema completo
alembic upgrade head
```

Hay **dos** migraciones generadas y revisadas manualmente (comentarios en
español dentro de cada archivo explicando qué se verificó):

| Migración | Contenido |
|---|---|
| `c655164696d9` | Esquema inicial: todas las tablas **excepto** `genero`, y `libro` **sin** `genero_id`. |
| `54bcabc30088` | Agrega la tabla `genero`, la columna `libro.genero_id`, su índice `ix_libro_genero_id` y la FK `fk_libro_genero_id`. |

`downgrade()` revierte en orden correcto (primero la segunda, luego la primera).

## 5. Datos iniciales (seed)

```bash
python -m app.seed
# o directamente
./app/seed.py
```

Limpia **todas** las tablas (`TRUNCATE ... RESTART IDENTITY CASCADE`, los
nombres salen de `SQLModel.metadata`, nunca de input externo) y deja un estado
conocido con ids fijos:

```
Seed aplicado correctamente:
  editoriales: 1 Emecé Editores, 2 Editorial Anagrama
  géneros:     1 Novela, 2 Cuento
  autores:     1 Cortázar, 2 Bioy Casares, 3 Borges
  libros:      1 Rayuela (25000.00), 2 Respiración artificial (27000.00), 3 Ficciones (18500.00)
  clientes:    1 Tomás Ríos, 2 María Gómez (con perfil)
  venta:       #1 de 1 total 62000.00
```

## 6. Arranque

```bash
uvicorn app.main:app --reload
```

Docs interactivas: <http://localhost:8000/docs>

Health checks:

- `GET /health/live` → 200 (proceso vivo)
- `GET /health/ready` → 200 si la BD responde a `SELECT 1`

## 7. Casos de prueba

Abrí **`test/casos_prueba.http`** con la extensión *REST Client* de VS Code.
Documenta con comentarios el resultado esperado de los 8 casos obligatorios:

| Caso | Qué prueba | Esperado |
|---|---|---|
| **C-01** | Path param no entero (`GET /libros/abc`) | 422 |
| **C-02** | ISBN o email repetido | 409 + mensaje propio |
| **C-03** | Segundo perfil del mismo cliente | 409 |
| **C-04** | Libro con editorial/autor inexistente | 409 + mensaje propio |
| **C-05** | Venta con libro o cliente inexistente | 409 |
| **C-06** | Venta válida con dos renglones | 201, precios del servidor y total 64000.00 |
| **C-07** | Detalle de libro/venta | cantidad **fija** de consultas en consola |
| **C-08** | `titulo=' OR '1'='1` | 200 con `[]` |

## 8. Evidencia C-07 (pegar acá la salida de consola)

Con `DB_ECHO=True` en `.env` y el servidor corriendo (`uvicorn app.main:app`),
se pidió `GET /libros/1` y `GET /ventas/1`. Salida de consola (solo se muestran
las líneas de SQL y el acceso HTTP; los timestamps fueron abreviados):

```text
$ curl -s http://localhost:8000/libros/1
{"id":1,"isbn":"978-84-376-0494-7","titulo":"Rayuela","precio":"25000.00","stock":10,"editorial_id":1,"genero_id":1,"editorial":{"id":1,"nombre":"Emecé Editores","pais":"Argentina"},"genero":{"id":1,"nombre":"Novela"},"autores":[{"autor_id":1,"rol":"autor","orden":1,"autor":{"id":1,"nombre":"Julio Cortázar"}}]}

INFO sqlalchemy.engine.Engine SELECT libro.id, libro.isbn, libro.titulo, libro.precio, libro.stock, libro.editorial_id, libro.genero_id, editorial_1.id AS id_1, editorial_1.nombre, editorial_1.pais, genero_1.id AS id_2, genero_1.nombre AS nombre_1
FROM libro LEFT OUTER JOIN editorial AS editorial_1 ON editorial_1.id = libro.editorial_id LEFT OUTER JOIN genero AS genero_1 ON genero_1.id = libro.genero_id
WHERE libro.id = $1::INTEGER
INFO sqlalchemy.engine.Engine [generated in 0.00073s] (1,)
INFO sqlalchemy.engine.Engine SELECT libro_autor.libro_id, libro_autor.autor_id, libro_autor.rol, libro_autor.orden, autor_1.id, autor_1.nombre, autor_1.nacionalidad
FROM libro_autor LEFT OUTER JOIN autor AS autor_1 ON autor_1.id = libro_autor.autor_id
WHERE libro_autor.libro_id IN ($1::INTEGER)
INFO sqlalchemy.engine.Engine [generated in 0.00115s] (1,)
INFO:     127.0.0.1:48352 - "GET /libros/1 HTTP/1.1" 200 OK

$ curl -s http://localhost:8000/ventas/1
{"id":1,"fecha":"2026-10-18T05:05:49.258213Z","total":"62000.00","cliente":{"id":1,"nombre":"Tomás Ríos","email":"tomas.rios@correo.com"},"renglones":[{"libro_id":1,"titulo":"Rayuela","cantidad":1,"precio_unitario":"25000.00","subtotal":"25000.00"},{"libro_id":3,"titulo":"Ficciones","cantidad":2,"precio_unitario":"18500.00","subtotal":"37000.00"}]}

INFO sqlalchemy.engine.Engine SELECT venta.id, venta.cliente_id, venta.fecha, venta.total, cliente_1.id AS id_1, cliente_1.nombre, cliente_1.email
FROM venta LEFT OUTER JOIN cliente AS cliente_1 ON cliente_1.id = venta.cliente_id
WHERE venta.id = $1::INTEGER
INFO sqlalchemy.engine.Engine [generated in 0.00070s] (1,)
INFO sqlalchemy.engine.Engine SELECT renglon_venta.venta_id, renglon_venta.id, renglon_venta.libro_id, renglon_venta.cantidad, renglon_venta.precio_unitario, libro_1.id, libro_1.isbn, libro_1.titulo, libro_1.precio, libro_1.stock, libro_1.editorial_id, libro_1.genero_id
FROM renglon_venta LEFT OUTER JOIN libro AS libro_1 ON libro_1.id = renglon_venta.libro_id
WHERE renglon_venta.venta_id IN ($1::INTEGER)
INFO sqlalchemy.engine.Engine [generated in 0.00137s] (1,)
INFO:     127.0.0.1:48364 - "GET /ventas/1 HTTP/1.1" 200 OK
```

**Lectura del resultado:**

- `GET /libros/1` → **exactamente 2 consultas**: (1) el libro con `LEFT JOIN`
  a editorial y género, (2) las autorías con `LEFT JOIN` a autores usando
  `IN (...)`. Cantidad fija, crece con el número de autores **0** veces.
- `GET /ventas/1` → **exactamente 2 consultas**: (1) la venta con `LEFT JOIN`
  al cliente, (2) los renglones con `LEFT JOIN` a los libros usando `IN (...)`.
- Sin N+1: ninguna consulta adicional por cada autor, libro o renglón.

---

## Estructura del proyecto

```
.
├── alembic.ini                  # sin credenciales (URL inyectada desde settings)
├── app/
│   ├── main.py                  # lifespan (motor en app.state) + registro de routers
│   ├── models.py                # centralizador de tablas (lo usa Alembic)
│   ├── seed.py                  # estado inicial conocido
│   ├── core/
│   │   ├── config.py            # Settings (pydantic-settings, .env)
│   │   ├── database.py          # engine async + async_sessionmaker + get_session
│   │   └── pagination.py        # limit/offset válidos (RN-10)
│   └── modules/
│       ├── health/              # /health/live y /health/ready
│       ├── editoriales/         # models, schemas, service, router
│       ├── generos/
│       ├── autores/
│       ├── libros/
│       ├── clientes/
│       └── ventas/
├── migrations/                  # async Alembic (-t async)
├── test/casos_prueba.http       # C-01 .. C-08
├── requirements.txt
└── .env.example
```

## Endpoints

| Método | Ruta | Códigos |
|---|---|---|
| POST | `/editoriales/` | 201, 409, 422 |
| GET | `/editoriales/` | 200, 422 |
| GET | `/editoriales/{id}` | 200, 404, 422 |
| PATCH | `/editoriales/{id}` | 200, 404, 409 |
| GET | `/editoriales/{id}/libros` | 200, 404 |
| POST | `/generos/` | 201, 409, 422 |
| GET | `/generos/` | 200, 422 |
| GET | `/generos/{id}/libros` | 200, 404 |
| POST | `/autores/` | 201, 422 |
| GET | `/autores/{id}` | 200, 404, 422 |
| PATCH | `/autores/{id}` | 200, 404, 422 |
| GET | `/autores/{id}/libros` | 200, 404 |
| POST | `/libros/` | 201, 409, 422 |
| GET | `/libros/` | 200, 422 |
| GET | `/libros/{id}` | 200, 404, 422 |
| PATCH | `/libros/{id}` | 200, 404, 409, 422 |
| POST | `/clientes/` | 201, 409, 422 |
| GET | `/clientes/{id}` | 200, 404, 422 |
| PATCH | `/clientes/{id}` | 200, 404, 409, 422 |
| POST | `/clientes/{id}/perfil` | 201, 404, 409 |
| PATCH | `/clientes/{id}/perfil` | 200, 404, 422 *(extra)* |
| GET | `/clientes/{id}/ventas` | 200, 404, 422 |
| POST | `/ventas/` | 201, 409, 422 |
| GET | `/ventas/` | 200, 422 |
| GET | `/ventas/{id}` | 200, 404, 422 |

> **RN-08**: no existe `PATCH`/`PUT` de ventas (son inmutables) → 405.
