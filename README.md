# EasyRent

EasyRent is a Django REST API for a housing rental service. The project will
support property listings, search and filtering, bookings, reviews, and user
roles for tenants and landlords.

## Technology stack

- Python 3.13
- Django and Django REST Framework
- Simple JWT authentication
- SQLite for local development
- MySQL for the main database
- drf-spectacular for OpenAPI and Swagger documentation

## Local setup

Create and activate a virtual environment:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Create the local environment file from the example:

```powershell
Copy-Item .env.example .env
```

Replace the placeholder values in `.env`, then run the Django checks and
migrations:

```powershell
python manage.py check
python manage.py migrate
```

Start the development server:

```powershell
python manage.py runserver
```

## Database selection

The `USE_REMOTE` variable in `.env` controls the database:

- `USE_REMOTE=False` uses local SQLite.
- `USE_REMOTE=True` uses the configured MySQL database.

## API documentation

After starting the server, the generated documentation is available at:

- Swagger UI: `http://127.0.0.1:8000/api/v1/docs/`
- OpenAPI schema: `http://127.0.0.1:8000/api/v1/schema/`

## Current status

The project foundation and application structure are prepared. Business models
and API endpoints are under development.
