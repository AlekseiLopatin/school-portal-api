"""Subject endpoints."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

import crud
import schemas
from database import get_db

router = APIRouter(prefix="/subjects", tags=["subjects"])


@router.get("", response_model=list[schemas.SubjectRead])
async def list_subjects(db: Session = Depends(get_db)):
    """List all subjects."""
    return crud.list_subjects(db)


@router.post(
    "",
    response_model=schemas.SubjectRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_subject(
    payload: schemas.SubjectCreate,
    db: Session = Depends(get_db),
):
    """Create a new subject."""
    return crud.create_subject(db, payload)
