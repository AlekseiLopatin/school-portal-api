"""
SQLAlchemy ORM models — the database tables.

Three tables for the Mini-Gradebook:
    - Student  : who you are tracking
    - Subject  : what subjects exist (Math, English, etc.)
    - Grade    : a single score for one student, one subject, one semester
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    grade_level = Column(String, nullable=False)  # e.g. "5A", "5B"

    grades = relationship(
        "Grade", back_populates="student", cascade="all, delete-orphan"
    )


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)

    grades = relationship("Grade", back_populates="subject")


class Grade(Base):
    __tablename__ = "grades"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    score = Column(Float, nullable=False)            # 0.0 to 100.0
    semester = Column(String, nullable=False)        # e.g. "2026-S1"
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="grades")
    subject = relationship("Subject", back_populates="grades")
