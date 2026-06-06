"""
School Portal API — FastAPI rebuild of the School Portal API layer.

A learning project: same domain as the original (students, subjects, grades)
but built from scratch in FastAPI with SQLAlchemy + SQLite, to learn the
React-plus-FastAPI stack hands-on.
"""
from fastapi import FastAPI

from database import Base, engine
from routers import grades, students, subjects
from fastapi.middleware.cors import CORSMiddleware

# Create database tables on startup.
# For production, replace this with Alembic migrations.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="School Portal API",
    description=(
        "REST API for a multilingual school-management system. "
        "FastAPI rebuild of the School Portal Supabase backend, "
        "for learning the React + FastAPI + PostgreSQL stack hands-on."
    ),
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev server (default)
        "http://localhost:3000",   # Common alt (Next.js, CRA)
        "https://school-portal-frontend-iota.vercel.app"  
        "https://school-portal-frontend-git-master-aleksei-lopatin-s-projects.vercel.app"
        "https://school-portal-frontend-9yf9ptuy4-aleksei-lopatin-s-projects.vercel.app"
        "https://gradebook.alekseilopatin.com" 
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["health"])
async def root():
    return {"message": "School Portal API is running"}


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}


# Register routers
app.include_router(students.router)
app.include_router(subjects.router)
app.include_router(grades.router)
