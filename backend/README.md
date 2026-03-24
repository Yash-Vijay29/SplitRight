# SplitRight Backend

Django + DRF backend for the SplitRight expense-sharing app.

This backend implements the ER relationship set shown in your SplitRight blueprint image:
- User <-> Group membership via `group_members`
- Group -> Expense
- Expense -> ExpenseSplit
- Settlement between two users within a group

## Current Stage

Parts 1 to 8 are implemented for backend scope:
- Part 1: Foundation and schema
- Part 2: Auth and user APIs
- Part 3: Group and membership APIs
- Part 4: Expense creation + split validation
- Part 5: Settlement recording
- Part 6: Balance engine
- Part 7: Frontend integration console (served at `/`)
- Part 8: Hardening + tests + demo seed + docs + SQL appendix

## Tech Stack

- Python 3.10
- Django 5.2
- Django REST Framework
- JWT auth (`djangorestframework-simplejwt`)
- MySQL or SQLite (configurable by env)

## Environment Setup

1. Open terminal in project root.
2. Activate conda env:

```bash
conda activate SplitRight
```

3. Move to backend:

```bash
cd backend
```

4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. Configure env:

```bash
cp .env.example .env
```

6. Run migrations:

```bash
python manage.py migrate
```

7. Optional: create admin user:

```bash
python manage.py createsuperuser
```

## Database Mode

- SQLite default: no extra setup needed.
- MySQL: set `DB_ENGINE=mysql` and DB credentials in `.env`, then run migrations.

## Run Backend

```bash
python manage.py runserver
```

API root is under `/api/...`.

## API Surface

- `POST /api/auth/signup`
- `POST /api/auth/login`
- `GET /api/users/me`

- `POST /api/groups`
- `GET /api/groups`
- `GET /api/groups/{group_id}`
- `POST /api/groups/{group_id}/join`
- `GET /api/groups/{group_id}/members`

- `POST /api/groups/{group_id}/expenses`
- `GET /api/groups/{group_id}/expenses`
- `GET /api/groups/{group_id}/expenses/{expense_id}`

- `POST /api/groups/{group_id}/settlements`
- `GET /api/groups/{group_id}/settlements`

- `GET /api/groups/{group_id}/balances`
- `GET /api/groups/{group_id}/balances/pairwise`
- `GET /api/users/me/balances`

## Run Tests

```bash
python manage.py test
```

## Demo Dataset Commands

### Basic sample

```bash
python manage.py seed_basic_data
```

### Reproducible Part 8 demo dataset

```bash
python manage.py seed_demo_data
```

Reset and reseed deterministic demo data:

```bash
python manage.py seed_demo_data --reset
```

Demo users created (password: `Password123!`):
- `alice@example.com`
- `bob@example.com`
- `carol@example.com`
- `dan@example.com`

## Part 8 Verification Steps

1. Fresh setup

```bash
conda activate SplitRight
cd backend
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
```

2. Run full checks

```bash
python manage.py check
python manage.py test
```

3. Build reproducible demo data

```bash
python manage.py seed_demo_data --reset
```

4. Start app and validate demo flow

```bash
python manage.py runserver
```

Then verify in order:
- signup/login
- create/join groups
- add expense (equal and unequal)
- list expenses
- view balances and pairwise balances
- record settlement
- verify balances update

5. Optional SQL evaluation queries
- Run queries from `docs/sql_query_appendix.sql` against your DB.

## Notes and Assumptions

- JWT is required for protected endpoints.
- Monetary values are stored as `Decimal(12,2)` and validated as non-negative / positive per model.
- Model-level validations enforce key membership constraints in addition to API checks.
