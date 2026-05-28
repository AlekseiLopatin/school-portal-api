"""Student endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import crud
import schemas
from database import get_db

router = APIRouter(prefix="/students", tags=["students"])


@router.get("", response_model=list[schemas.StudentRead])
async def list_students(db: Session = Depends(get_db)):
    """List all students."""
    return crud.list_students(db)


@router.post(
    "",
    response_model=schemas.StudentRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_student(
    payload: schemas.StudentCreate,
    db: Session = Depends(get_db),
):
    """Create a new student."""
    return crud.create_student(db, payload)


@router.get("/{student_id}", response_model=schemas.StudentRead)
async def get_student(student_id: int, db: Session = Depends(get_db)):
    """Get a single student by id."""
    student = crud.get_student(db, student_id)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student {student_id} not found",
        )
    return student


@router.get("/{student_id}/summary", response_model=schemas.StudentSummary)
async def student_summary(
    student_id: int,
    semester: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Average score per subject for one student. Optionally scope by semester:

        GET /students/3/summary?semester=2026-S1
    """
    summary = crud.student_summary(db, student_id, semester)
    if summary is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student {student_id} not found",
        )
    return summary
