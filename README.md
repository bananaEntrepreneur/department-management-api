# Department Management API

API for managing company departments and employees.

The project is built with:

- `FastAPI` for the HTTP API
- `SQLAlchemy` for database access
- `PostgreSQL` as the main database
- `Alembic` for migrations
- `sqladmin` for the admin panel
- `pytest` for unit, integration, and end-to-end tests

## Features

- Create departments
- Create employees inside a department
- Validate parent department existence when creating records
- Validate incoming payloads at the schema layer

## Project Structure

- `app/api` - HTTP routes
- `app/services` - business logic
- `app/repositories` - data access
- `app/models` - SQLAlchemy models
- `app/schemas` - Pydantic schemas
- `migrations` - Alembic migrations
- `tests` - unit, integration, and end-to-end tests

## Environment Variables

The application reads its configuration from a `.env` file.

1. Copy the example file:

```bash
cp .env.example .env
```

2. Update the values if needed:

- `DB_USER` - PostgreSQL username
- `DB_PASSWORD` - PostgreSQL password
- `DB_NAME` - database name
- `DB_HOST` - database host
- `DB_PORT` - database port

## Run With Docker Compose

1. Build and start the containers:

```bash
docker compose up --build
```

2. After startup:

- API is available at `http://localhost:8001`
- Admin panel is available at `http://localhost:8001/admin`
- PostgreSQL is available at `localhost:5433`

3. Stop the environment:

```bash
docker compose down
```

To remove PostgreSQL data as well:

```bash
docker compose down -v
```

## Tests

The project uses `uv` to run Python commands.

### Run all tests

```bash
uv run pytest
```

## Migrations

Migrations live in the `migrations` directory.

To apply them manually:

```bash
uv run alembic upgrade head
```

## Main Endpoints

- `GET /` - basic service check
- `POST /departments/` - create a department
- `POST /departments/{id}/employees/` - create an employee inside a department

