"""Grade endpoints."""
from typing import Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

import crud
import schemas
from database import get_db

router = APIRouter(prefix="/grades", tags=["grades"])


@router.get("", response_model=list[schemas.GradeRead])
async def list_grades(
    student_id: Optional[int] = None,
    subject_id: Optional[int] = None,
    semester: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    List grades. All three filters are optional and can be combined:

        GET /grades?student_id=3
        GET /grades?student_id=3&semester=2026-S1
        GET /grades?subject_id=1&semester=2026-S1
    """
    return crud.list_grades(db, student_id, subject_id, semester)


@router.post(
    "",
    response_model=schemas.GradeRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_grade(
    payload: schemas.GradeCreate,
    db: Session = Depends(get_db),
):
    """Record a new grade for a student in a subject in a semester."""
    return crud.create_grade(db, payload)
