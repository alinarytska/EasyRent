# EasyRent

EasyRent is a Django REST Framework backend for a housing rental service.

The project provides API endpoints for property listings, listing images,
booking management, reviews, search history, view history, user authentication
and role-based permissions.

## Technology stack

- Python 3.13
- Django 6
- Django REST Framework
- Simple JWT authentication
- MySQL as the main database
- SQLite for optional local development
- django-filter for backend filtering
- drf-spectacular for OpenAPI and Swagger documentation
- Pillow for listing image validation and processing
- WhiteNoise for static files
- Docker and Docker Compose

## Project structure

The project is split into separate Django apps inside the `apps` package:

- `users` - custom user model, registration, JWT auth, profile actions, groups
- `listings` - property listings, listing images, filtering, search, popularity
- `bookings` - booking creation, price snapshot, status actions
- `reviews` - ratings and reviews for completed bookings
- `search_history` - saved search queries and popular searches
- `view_history` - listing view history and popular listings
- `common` - shared base model and mixins

Each main app keeps models, serializers, views, services, permissions, filters
and urls separated by responsibility.

## Environment files

The project uses environment variables for private settings.

Local Django run:

```bash
cp .env.example .env
```

Docker run:

```bash
cp .env.docker.example .env.docker
```

Files that must not be committed:

- `.env`
- `.env.docker`

Example files are safe to commit:

- `.env.example`
- `.env.docker.example`

## Local setup without Docker

Create and activate a virtual environment:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Create `.env` from the example:

```powershell
Copy-Item .env.example .env
```

Run checks and migrations:

```powershell
python manage.py check
python manage.py migrate
```

Create a superuser if needed:

```powershell
python manage.py createsuperuser
```

Start the development server:

```powershell
python manage.py runserver
```

## Database selection

The `USE_REMOTE` variable controls the database:

```env
USE_REMOTE=False
```

uses local SQLite.

```env
USE_REMOTE=True
```

uses MySQL settings from the environment file.

## Docker setup

Create the Docker environment file:

```bash
cp .env.docker.example .env.docker
```

Build and start the project:

```bash
docker compose up --build -d
```

For later starts, when Docker files and dependencies did not change:

```bash
docker compose up -d
```

Stop containers without deleting database volumes:

```bash
docker compose down
```

Check container status:

```bash
docker compose ps
```

Run Django checks inside Docker:

```bash
docker compose exec web python manage.py check
```

## Docker seed data

The project includes a management command for demo data:

```bash
python manage.py seed_data --clear
```

Inside Docker:

```bash
docker compose exec web python manage.py seed_data --clear
```

To seed the database automatically on container startup, set in `.env.docker`:

```env
SEED_DATA_ON_STARTUP=True
SEED_DATA_ARGS=--clear
```

After the database is filled, it is better to disable automatic seeding:

```env
SEED_DATA_ON_STARTUP=False
SEED_DATA_ARGS=
```

## Docker superuser creation

The project includes a safe command that creates a superuser only if it does
not already exist:

```bash
python manage.py create_superuser_if_not_exists
```

For automatic Docker startup creation, set in `.env.docker`:

```env
CREATE_SUPERUSER_ON_STARTUP=True
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=StrongAdminPassword123!
DJANGO_SUPERUSER_FIRST_NAME=Admin
DJANGO_SUPERUSER_LAST_NAME=User
```

After the first successful creation, it is recommended to disable it:

```env
CREATE_SUPERUSER_ON_STARTUP=False
```

## API documentation

After starting the server, API documentation is available at:

- Swagger UI: `http://127.0.0.1:8000/api/v1/docs/`
- OpenAPI schema: `http://127.0.0.1:8000/api/v1/schema/`

The project root redirects to Swagger:

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/api/v1/`

## Main API endpoints

Authentication:

- `POST /api/v1/auth/token/`
- `POST /api/v1/auth/token/refresh/`
- `POST /api/v1/auth/logout/`

Users:

- `POST /api/v1/users/register/`
- `GET /api/v1/users/me/`
- `PATCH /api/v1/users/me/`
- `DELETE /api/v1/users/me/`
- `POST /api/v1/users/me/change-password/`
- `POST /api/v1/users/me/groups/`
- `POST /api/v1/users/reactivate/`

Listings:

- `GET /api/v1/listings/`
- `POST /api/v1/listings/`
- `GET /api/v1/listings/{id}/`
- `PATCH /api/v1/listings/{id}/`
- `DELETE /api/v1/listings/{id}/`
- `GET /api/v1/listings/my/`
- `GET /api/v1/listings/popular/`
- `GET /api/v1/listings/{id}/reviews/`

Listing images:

- `GET /api/v1/listings/images/`
- `POST /api/v1/listings/images/`
- `GET /api/v1/listings/images/{id}/`
- `PATCH /api/v1/listings/images/{id}/`
- `DELETE /api/v1/listings/images/{id}/`

Bookings:

- `GET /api/v1/bookings/`
- `POST /api/v1/bookings/`
- `GET /api/v1/bookings/my/`
- `POST /api/v1/bookings/{id}/confirm/`
- `POST /api/v1/bookings/{id}/reject/`
- `POST /api/v1/bookings/{id}/cancel/`

Reviews:

- `GET /api/v1/reviews/`
- `POST /api/v1/reviews/`
- `GET /api/v1/reviews/my/`

History and popularity:

- `GET /api/v1/search-history/`
- `GET /api/v1/search-history/popular/`
- `GET /api/v1/view-history/`
- `GET /api/v1/view-history/popular-listings/`

## Listing filtering examples

Search by keyword:

```text
GET /api/v1/listings/?search=Berlin
```

Filter by city and price:

```text
GET /api/v1/listings/?city=Berlin&min_price=100&max_price=200
```

Filter by rooms:

```text
GET /api/v1/listings/?min_rooms=2&max_rooms=4
```

Sort by price:

```text
GET /api/v1/listings/?ordering=price_per_night
GET /api/v1/listings/?ordering=-price_per_night
```

Sort by popularity:

```text
GET /api/v1/listings/?ordering=-views_count
```

## Permissions overview

- Anonymous users can view active listings and listing reviews.
- Only users in the `Landlords` group can create listings.
- Listing owners can update or delete their own listings.
- Only listing owners can manage listing images.
- Only users in the `Renters` group can create bookings.
- Landlords can confirm or reject bookings for their own listings.
- Renters can cancel their own bookings before the cancellation deadline.
- Reviews can be created only for the renter's own completed booking.
- Search and view history are read-only for users and are created automatically.
- Staff users manage all data through Django Admin, not through special API access.

## Tests

Run the full test suite:

```powershell
python manage.py test
```

Run tests inside Docker:

```bash
docker compose exec web python manage.py test
```

Current local verification:

```text
207 tests passed
python manage.py check passed
python manage.py makemigrations --check --dry-run passed
OpenAPI schema validation passed
```

## Admin panel

The Django Admin panel is available at:

```text
http://127.0.0.1:8000/admin/
```

Admin configuration includes search, filters, date hierarchy and read-only
fields for business objects that should be managed through the API.

## Deployment status

Docker Compose configuration is prepared for local containerized deployment.

AWS EC2 deployment is planned as the final deployment target.
