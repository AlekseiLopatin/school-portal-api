"""
Pydantic schemas — request and response shapes.

FastAPI uses these to validate incoming data and shape outgoing responses.

Naming convention:
    *Base    : fields shared by Create and Read
    *Create  : request body for POST endpoints (no id, no created_at)
    *Read    : response body returned to clients (with id, computed fields)
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ---- Student ---------------------------------------------------------------

class StudentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    grade_level: str = Field(..., min_length=1, max_length=10)


class StudentCreate(StudentBase):
    pass


class StudentRead(StudentBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class StudentUpdate(BaseModel):
    """Partial update, every field optional."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    grade_level: Optional[str] = Field(None, min_length=1, max_length=10)

    
# ---- Subject ---------------------------------------------------------------

class SubjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class SubjectCreate(SubjectBase):
    pass


class SubjectRead(SubjectBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# ---- Grade -----------------------------------------------------------------

class GradeBase(BaseModel):
    student_id: int
    subject_id: int
    score: float = Field(..., ge=0.0, le=100.0)
    semester: str = Field(..., min_length=4, max_length=20)


class GradeCreate(GradeBase):
    pass


class GradeRead(GradeBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---- Computed summary ------------------------------------------------------

class SubjectAverage(BaseModel):
    subject_id: int
    subject_name: str
    average_score: float
    grade_count: int


class StudentSummary(BaseModel):
    student_id: int
    student_name: str
    semester: Optional[str] = None
    subjects: list[SubjectAverage]
