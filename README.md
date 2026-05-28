# School Portal API

REST API rebuild of the [School Portal](https://github.com/AlekseiLopatin/school-website) backend in **FastAPI + SQLAlchemy + SQLite**. Built to learn the React-plus-FastAPI stack hands-on by re-implementing a familiar domain end-to-end.

## Stack

- **FastAPI** — REST framework, type-hint-driven
- **SQLAlchemy 2.0** — ORM
- **SQLite** — local development DB (single file, no setup); swap to PostgreSQL for production
- **Pydantic v2** — request/response validation

## Quick start

```bash
# 1. Activate your virtual environment
.venv\Scripts\Activate.ps1     # Windows PowerShell
# source .venv/bin/activate    # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the dev server
uvicorn main:app --reload

# 4. Open the interactive docs
# http://127.0.0.1:8000/docs
```

## Data model

Three tables, deliberately small:

- **students** — `id`, `name`, `grade_level`
- **subjects** — `id`, `name`
- **grades** — `id`, `student_id`, `subject_id`, `score`, `semester`, `created_at`

## Endpoints

| Method | Path | What it does |
|---|---|---|
| `GET` | `/students` | List all students |
| `POST` | `/students` | Create a student |
| `GET` | `/students/{id}` | One student |
| `GET` | `/students/{id}/summary?semester=...` | Average score per subject for a student |
| `GET` | `/subjects` | List all subjects |
| `POST` | `/subjects` | Create a subject |
| `GET` | `/grades?student_id=&subject_id=&semester=` | List grades, filterable |
| `POST` | `/grades` | Record a grade |

## Project structure

```
.
├── main.py              # FastAPI app, router registration, table creation
├── database.py          # SQLAlchemy engine + session dependency
├── models.py            # SQLAlchemy ORM models (DB tables)
├── schemas.py           # Pydantic request/response schemas
├── crud.py              # Database operations (service layer)
├── routers/
│   ├── __init__.py
│   ├── students.py      # Student endpoints
│   ├── subjects.py      # Subject endpoints
│   └── grades.py        # Grade endpoints
├── requirements.txt
└── README.md
```

## Roadmap

- [ ] Auth (JWT)
- [ ] Alembic migrations (replace `Base.metadata.create_all`)
- [ ] PostgreSQL connection (replace SQLite)
- [ ] Deploy to Railway or Fly.io
- [ ] Point the School Portal React frontend at this backend
