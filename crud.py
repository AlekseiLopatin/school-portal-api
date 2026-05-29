"""
Database operations — the "service layer" between routers and the ORM.

Keeping these functions out of the routers means each router file stays focused
on HTTP concerns (status codes, validation, error handling) while crud.py
concentrates the database logic. It also makes the database operations easy to
unit-test without spinning up FastAPI itself.
"""
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

import models
import schemas


# ---- Students --------------------------------------------------------------

def list_students(db: Session) -> list[models.Student]:
    return db.query(models.Student).all()


def get_student(db: Session, student_id: int) -> Optional[models.Student]:
    return db.query(models.Student).filter(models.Student.id == student_id).first()


def create_student(db: Session, payload: schemas.StudentCreate) -> models.Student:
    student = models.Student(**payload.model_dump())
    db.add(student)
    db.commit()
    db.refresh(student)
    return student

def delete_student(db: Session, student_id: int) -> bool:
    student = get_student(db, student_id)
    if student is None:
        return False
    db.delete(student)
    db.commit()
    return True

def update_student(db: Session, student_id: int, payload:schemas.StudentUpdate,) -> Optional[models.Student]:
    student = get_student(db, student_id)
    if student is None:
        return None
    # exclude_unset=True is the KEY idea - we only get the fields
    # the user actually sent, not the ones that defaulted to None
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(student, field, value)
    db.commit()
    db.refresh(student)
    return student


# ---- Subjects --------------------------------------------------------------

def list_subjects(db: Session) -> list[models.Subject]:
    return db.query(models.Subject).all()


def create_subject(db: Session, payload: schemas.SubjectCreate) -> models.Subject:
    subject = models.Subject(**payload.model_dump())
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject


# ---- Grades ----------------------------------------------------------------

def list_grades(
    db: Session,
    student_id: Optional[int] = None,
    subject_id: Optional[int] = None,
    semester: Optional[str] = None,
) -> list[models.Grade]:
    q = db.query(models.Grade)
    if student_id is not None:
        q = q.filter(models.Grade.student_id == student_id)
    if subject_id is not None:
        q = q.filter(models.Grade.subject_id == subject_id)
    if semester is not None:
        q = q.filter(models.Grade.semester == semester)
    return q.all()


def create_grade(db: Session, payload: schemas.GradeCreate) -> models.Grade:
    grade = models.Grade(**payload.model_dump())
    db.add(grade)
    db.commit()
    db.refresh(grade)
    return grade


# ---- Computed: per-subject averages for one student ------------------------

def student_summary(
    db: Session,
    student_id: int,
    semester: Optional[str] = None,
) -> Optional[schemas.StudentSummary]:
    student = get_student(db, student_id)
    if student is None:
        return None

    q = (
        db.query(
            models.Subject.id.label("subject_id"),
            models.Subject.name.label("subject_name"),
            func.avg(models.Grade.score).label("avg_score"),
            func.count(models.Grade.id).label("grade_count"),
        )
        .join(models.Grade, models.Grade.subject_id == models.Subject.id)
        .filter(models.Grade.student_id == student_id)
    )
    if semester is not None:
        q = q.filter(models.Grade.semester == semester)
    q = q.group_by(models.Subject.id, models.Subject.name)

    subjects = [
        schemas.SubjectAverage(
            subject_id=row.subject_id,
            subject_name=row.subject_name,
            average_score=round(row.avg_score, 2),
            grade_count=row.grade_count,
        )
        for row in q.all()
    ]

    return schemas.StudentSummary(
        student_id=student.id,
        student_name=student.name,
        semester=semester,
        subjects=subjects,
    )
