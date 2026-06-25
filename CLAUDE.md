# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Stack

Django 5 + DRF + SimpleJWT + Celery 5 backend, React 18 + Vite 5 + Tailwind + TanStack Query frontend, Redis as broker/cache, SQLite as the default DB. Whole stack runs via `docker compose up --build` (5 services: `redis`, `backend`, `worker`, `beat`, `frontend`).

## Common commands

Docker (preferred — `backend` auto-migrates and re-seeds on every boot):

```bash
docker compose up --build                          # full stack on :5173 (frontend) and :8000 (backend)
docker compose logs -f backend worker beat
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py shell
docker compose exec backend python manage.py test <app>        # run a single app's tests
docker compose exec backend python manage.py test <app>.tests.SomeTest.test_x
docker compose down -v                             # nuke DB + redis + media
```

Local backend (Python 3.10+, Redis on 6379):

```powershell
cd backend
python -m venv .venv ; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py seed_exercises ; python manage.py seed_foods ; python manage.py seed_achievements
python manage.py runserver
# in separate shells:
celery -A fitness_tracker worker -l info
celery -A fitness_tracker beat -l info
```

Local frontend:

```powershell
cd frontend
npm install
npm run dev          # http://localhost:5173, proxies /api → backend
npm run build        # production bundle
```

There is no lint/format script wired up in either package; don't invent one.

## Architecture — things you can't see by reading one file

### Backend app layout

Each domain is a Django app under `backend/`: `accounts`, `exercises`, `workouts`, `nutrition`, `measurements`, `goals`, `social`, `achievements`, `reminders`. They're mounted at `/api/v1/<app>/` from `fitness_tracker/urls.py`. Custom user model: `accounts.User` (set via `AUTH_USER_MODEL`).

Auth is JWT (SimpleJWT) with refresh-token rotation. Everything except `register` / `login` / `refresh` requires `Authorization: Bearer <access>`.

### Celery topology

Three roles share one image, dispatched by `backend/entrypoint.sh {web|worker|beat|migrate}`:

- `web` — waits for Redis, runs `migrate`, runs idempotent seed commands (`seed_exercises`, `seed_foods`, `seed_achievements`), then `runserver` (DEBUG) or `gunicorn` (else).
- `worker` — `celery -A fitness_tracker worker`.
- `beat` — `celery -A fitness_tracker beat` using `django_celery_beat.schedulers:DatabaseScheduler` (so periodic schedules live in the DB; migrations must run first).

Static beat schedule is defined in `fitness_tracker/settings.py → CELERY_BEAT_SCHEDULE`:

| Cron                  | Task                                       |
|-----------------------|--------------------------------------------|
| every minute          | `reminders.tasks.dispatch_due_reminders`   |
| daily 02:15 UTC       | `achievements.tasks.decay_inactive_streaks` |
| daily 02:30 UTC       | `goals.tasks.mark_expired_goals`           |
| Mondays 08:00 UTC     | `accounts.tasks.build_weekly_summaries`    |

Set `CELERY_TASK_ALWAYS_EAGER=True` in `.env` to run tasks inline (useful for tests).

The reminders **delivery** layer in `reminders.tasks.deliver_reminder` is intentionally a `logger.info` stub — swap it for push/email/websocket when needed. The dispatcher is wired.

### Caching contract (important — don't bypass)

All cache keys + TTLs live in **`fitness_tracker/cache_keys.py`**. Read paths and the per-app `signals.py` modules import from there — if you add a cached read, add the key here and a matching invalidation signal. Do not hardcode cache key strings elsewhere.

`django-redis` is configured with `IGNORE_EXCEPTIONS=True`, so a Redis outage degrades caching silently rather than 500-ing the API. Don't change this without a reason.

Cached paths today: exercise catalog (24h), achievement catalog (24h), public foods (6h), per-user workout stats (5m), per-user-per-date nutrition summary (2m), per-user streak (5m), per-user weekly summary (~8d, rewritten by Mon beat task).

### Frontend data flow

`frontend/src/api/client.js` is an axios instance with a JWT refresh interceptor; `endpoints.js` wraps each REST resource. Server state is **TanStack Query** — mutations must invalidate the relevant query keys so the UI stays consistent without manual refetches. `AuthContext` (in `contexts/`) holds the access token and current user.

Vite dev server proxies `/api` and `/media` to `VITE_API_PROXY_TARGET` (defaults to `http://backend:8000` inside compose, `http://127.0.0.1:8000` locally). File watching uses polling — required for hot-reload across the Windows/macOS bind mount.

### Seeds and SQLite

Seeds use `update_or_create`, so re-running them is safe. The SQLite DB lives at `backend/db.sqlite3` and is bind-mounted from the host (`./backend:/app` in compose), so it survives `docker compose down` but is wiped by `docker compose down -v` (named volumes go too).

To switch to Postgres: add a `postgres` service, point `DATABASES["default"]` at it, drop the SQLite file. No other code changes needed (per README).

## graphify

This project has a live knowledge graph at `graphify-out/` covering all backend and frontend source. It is the **primary navigation tool** — use it before reaching for grep, glob, or raw file reads.

### Step 1 — Orient before every task

Before reading any source file, running a search, or answering an architecture question:

1. Read **`graphify-out/GRAPH_REPORT.md`** — god nodes, community clusters, cross-file edges at a glance.

### Step 2 — Search with graphify, not grep

| When you need to… | Use |
|---|---|
| Understand how a feature/module works | `graphify query "<question>"` |
| Trace a call chain or data flow | `graphify query "<question>" --dfs` |
| Find the shortest link between two concepts | `graphify path "<A>" "<B>"` |
| Get a plain-English explanation of a node | `graphify explain "<concept>"` |
| Wide context sweep | `graphify query "<question>" --budget 1500` |

Only fall back to `Grep` / `Glob` when you need an exact symbol name or line number that graphify doesn't return.

### Step 3 — Keep the graph current after edits

Run **`graphify update .`** after every batch of file edits (AST-only, no API cost, ~2 s). A `PostToolUse` hook in `.claude/settings.json` fires this automatically after each `Edit` or `Write` call. If you make several changes before querying, or the hook fails, run it manually:

```bash
graphify update .
```

### Python Conventions

- Type hints on all function signatures — use `from __future__ import annotations`
- No `print()` statements — use `logging.getLogger(__name__)`
- f-strings for string formatting, never `%` or `.format()`
- Use `pathlib.Path` not `os.path` for file operations
- Imports sorted with isort: stdlib, third-party, local (enforced by ruff)

### Database

- All queries use Django ORM — raw SQL only with `.raw()` and parameterized queries
- Migrations committed to git — never use `--fake` in production
- Use `select_related()` and `prefetch_related()` to prevent N+1 queries
- All models must have `created_at` and `updated_at` auto-fields
- Indexes on any field used in `filter()`, `order_by()`, or `WHERE` clauses

```python
# BAD: N+1 query
orders = Order.objects.all()
for order in orders:
    print(order.customer.name)  # hits DB for each order

# GOOD: Single query with join
orders = Order.objects.select_related("customer").all()
```

### Authentication

- JWT via `djangorestframework-simplejwt` — access token (15 min) + refresh token (7 days)
- Permission classes on every view — never rely on default
- Use `IsAuthenticated` as base, add custom permissions for object-level access
- Token blacklisting enabled for logout

### Serializers

- Use `ModelSerializer` for simple CRUD, `Serializer` for complex validation
- Separate read and write serializers when input/output shapes differ
- Validate at serializer level, not in views — views should be thin

```python
class CreateOrderSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, max_value=100)

    def validate_product_id(self, value):
        if not Product.objects.filter(id=value, active=True).exists():
            raise serializers.ValidationError("Product not found or inactive")
        return value

class OrderDetailSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ["id", "customer", "product", "quantity", "total", "status", "created_at"]
```

### Error Handling

- Use DRF exception handler for consistent error responses
- Custom exceptions for business logic in `core/exceptions.py`
- Never expose internal error details to clients

```python
# core/exceptions.py
from rest_framework.exceptions import APIException

class InsufficientStockError(APIException):
    status_code = 409
    default_detail = "Insufficient stock for this order"
    default_code = "insufficient_stock"
```

### Code Style

- No emojis in code or comments
- Max line length: 120 characters (enforced by ruff)
- Classes: PascalCase, functions/variables: snake_case, constants: UPPER_SNAKE_CASE
- Views are thin — business logic lives in service functions or model methods

## File Structure

```
config/
  settings/
    base.py              # Shared settings
    local.py             # Dev overrides (DEBUG=True)
    production.py        # Production settings
  urls.py                # Root URL config
  celery.py              # Celery app configuration
apps/
  accounts/              # User auth, registration, profile
    models.py
    serializers.py
    views.py
    services.py          # Business logic
    tests/
      test_views.py
      test_services.py
      factories.py       # Factory Boy factories
  orders/                # Order management
    models.py
    serializers.py
    views.py
    services.py
    tasks.py             # Celery tasks
    tests/
  products/              # Product catalog
    models.py
    serializers.py
    views.py
    tests/
core/
  exceptions.py          # Custom API exceptions
  permissions.py         # Shared permission classes
  pagination.py          # Custom pagination
  middleware.py          # Request logging, timing
  tests/
```

## Key Patterns

### Service Layer

```python
# apps/orders/services.py
from django.db import transaction

def create_order(*, customer, product_id: uuid.UUID, quantity: int) -> Order:
    """Create an order with stock validation and payment hold."""
    product = Product.objects.select_for_update().get(id=product_id)

    if product.stock < quantity:
        raise InsufficientStockError()

    with transaction.atomic():
        order = Order.objects.create(
            customer=customer,
            product=product,
            quantity=quantity,
            total=product.price * quantity,
        )
        product.stock -= quantity
        product.save(update_fields=["stock", "updated_at"])

    # Async: send confirmation email
    send_order_confirmation.delay(order.id)
    return order
```

### View Pattern

```python
# apps/orders/views.py
class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination

    def get_serializer_class(self):
        if self.action == "create":
            return CreateOrderSerializer
        return OrderDetailSerializer

    def get_queryset(self):
        return (
            Order.objects
            .filter(customer=self.request.user)
            .select_related("product", "customer")
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        order = create_order(
            customer=self.request.user,
            product_id=serializer.validated_data["product_id"],
            quantity=serializer.validated_data["quantity"],
        )
        serializer.instance = order
```

### Test Pattern (pytest + Factory Boy)

```python
# apps/orders/tests/factories.py
import factory
from apps.accounts.tests.factories import UserFactory
from apps.products.tests.factories import ProductFactory

class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "orders.Order"

    customer = factory.SubFactory(UserFactory)
    product = factory.SubFactory(ProductFactory, stock=100)
    quantity = 1
    total = factory.LazyAttribute(lambda o: o.product.price * o.quantity)

# apps/orders/tests/test_views.py
import pytest
from rest_framework.test import APIClient

@pytest.mark.django_db
class TestCreateOrder:
    def setup_method(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.client.force_authenticate(self.user)

    def test_create_order_success(self):
        product = ProductFactory(price=29_99, stock=10)
        response = self.client.post("/api/orders/", {
            "product_id": str(product.id),
            "quantity": 2,
        })
        assert response.status_code == 201
        assert response.data["total"] == 59_98

    def test_create_order_insufficient_stock(self):
        product = ProductFactory(stock=0)
        response = self.client.post("/api/orders/", {
            "product_id": str(product.id),
            "quantity": 1,
        })
        assert response.status_code == 409

    def test_create_order_unauthenticated(self):
        self.client.force_authenticate(None)
        response = self.client.post("/api/orders/", {})
        assert response.status_code == 401
```

## Environment Variables

```bash
# Django
SECRET_KEY=
DEBUG=False
ALLOWED_HOSTS=api.example.com

# Database
DATABASE_URL=postgres://user:pass@localhost:5432/myapp

# Redis (Celery broker + cache)
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_ACCESS_TOKEN_LIFETIME=15       # minutes
JWT_REFRESH_TOKEN_LIFETIME=10080   # minutes (7 days)

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
```

## Testing Strategy

```bash
# Run all tests
pytest --cov=apps --cov-report=term-missing

# Run specific app tests
pytest apps/orders/tests/ -v

# Run with parallel execution
pytest -n auto

# Only failing tests from last run
pytest --lf
```

## ECC Workflow

```bash
# Planning
/plan "Add order refund system with Stripe integration"

# Development with TDD
/tdd                    # pytest-based TDD workflow

# Review
/python-review          # Python-specific code review
/security-scan          # Django security audit
/code-review            # General quality check

# Verification
/verify                 # Build, lint, test, security scan
```

## Git Workflow

- `feat:` new features, `fix:` bug fixes, `refactor:` code changes
- Feature branches from `main`, PRs required
- CI: ruff (lint + format), mypy (types), pytest (tests), safety (dep check)
- Deploy: Docker image, managed via Kubernetes or Railway
