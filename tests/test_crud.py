"""
Unit tests for crud.py — call functions directly against an isolated DB session.

These tests don't go through HTTP / FastAPI at all. They test the business logic
in `crud.py` as if calling library functions — which is what they are.

Each `class Test...` groups tests by the function area. Test names read as
plain English sentences describing one specific behaviour.
"""

import crud
import schemas


# ---- Students -----------------------------------------------------------

class TestStudents:
    def test_list_students_starts_empty(self, db_session):
        assert crud.list_students(db_session) == []

    def test_create_student_returns_student_with_id(self, db_session):
        payload = schemas.StudentCreate(name="Alice", grade_level="5A")
        student = crud.create_student(db_session, payload)
        assert student.id is not None
        assert student.name == "Alice"
        assert student.grade_level == "5A"

    def test_list_students_returns_all_created_students(self, db_session):
        crud.create_student(db_session, schemas.StudentCreate(name="Alice", grade_level="5A"))
        crud.create_student(db_session, schemas.StudentCreate(name="Bob", grade_level="5B"))
        students = crud.list_students(db_session)
        assert len(students) == 2
        assert {s.name for s in students} == {"Alice", "Bob"}

    def test_get_student_returns_none_when_not_found(self, db_session):
        assert crud.get_student(db_session, 999) is None

    def test_get_student_returns_existing_student(self, db_session):
        created = crud.create_student(
            db_session, schemas.StudentCreate(name="Alice", grade_level="5A")
        )
        fetched = crud.get_student(db_session, created.id)
        assert fetched.id == created.id
        assert fetched.name == "Alice"

    def test_update_student_changes_only_the_fields_sent(self, db_session):
        student = crud.create_student(
            db_session, schemas.StudentCreate(name="Alice", grade_level="5A")
        )
        # Only update grade_level; name should stay the same
        updated = crud.update_student(
            db_session, student.id, schemas.StudentUpdate(grade_level="5B")
        )
        assert updated.name == "Alice"
        assert updated.grade_level == "5B"

    def test_update_student_returns_none_when_not_found(self, db_session):
        result = crud.update_student(
            db_session, 999, schemas.StudentUpdate(name="Ghost")
        )
        assert result is None

    def test_delete_student_returns_true_when_found(self, db_session):
        student = crud.create_student(
            db_session, schemas.StudentCreate(name="Alice", grade_level="5A")
        )
        assert crud.delete_student(db_session, student.id) is True
        # And the student is actually gone
        assert crud.get_student(db_session, student.id) is None

    def test_delete_student_returns_false_when_not_found(self, db_session):
        assert crud.delete_student(db_session, 999) is False


# ---- Subjects -----------------------------------------------------------

class TestSubjects:
    def test_list_subjects_starts_empty(self, db_session):
        assert crud.list_subjects(db_session) == []

    def test_create_subject_returns_subject_with_id(self, db_session):
        subject = crud.create_subject(db_session, schemas.SubjectCreate(name="Math"))
        assert subject.id is not None
        assert subject.name == "Math"

    def test_list_subjects_returns_all_created(self, db_session):
        crud.create_subject(db_session, schemas.SubjectCreate(name="Math"))
        crud.create_subject(db_session, schemas.SubjectCreate(name="English"))
        subjects = crud.list_subjects(db_session)
        assert len(subjects) == 2
        assert {s.name for s in subjects} == {"Math", "English"}


# ---- Grades -------------------------------------------------------------

class TestGrades:
    def test_create_grade_returns_grade_with_id(self, db_session):
        student = crud.create_student(
            db_session, schemas.StudentCreate(name="Alice", grade_level="5A")
        )
        subject = crud.create_subject(db_session, schemas.SubjectCreate(name="Math"))
        grade = crud.create_grade(
            db_session,
            schemas.GradeCreate(
                student_id=student.id,
                subject_id=subject.id,
                score=85.0,
                semester="2026-S1",
            ),
        )
        assert grade.id is not None
        assert grade.score == 85.0

    def test_list_grades_with_no_filters_returns_all(self, db_session):
        student = crud.create_student(
            db_session, schemas.StudentCreate(name="Alice", grade_level="5A")
        )
        subject = crud.create_subject(db_session, schemas.SubjectCreate(name="Math"))
        crud.create_grade(
            db_session,
            schemas.GradeCreate(
                student_id=student.id, subject_id=subject.id,
                score=85.0, semester="2026-S1",
            ),
        )
        crud.create_grade(
            db_session,
            schemas.GradeCreate(
                student_id=student.id, subject_id=subject.id,
                score=90.0, semester="2026-S2",
            ),
        )
        assert len(crud.list_grades(db_session)) == 2

    def test_list_grades_filtered_by_student(self, db_session):
        alice = crud.create_student(
            db_session, schemas.StudentCreate(name="Alice", grade_level="5A")
        )
        bob = crud.create_student(
            db_session, schemas.StudentCreate(name="Bob", grade_level="5B")
        )
        subject = crud.create_subject(db_session, schemas.SubjectCreate(name="Math"))
        crud.create_grade(
            db_session,
            schemas.GradeCreate(
                student_id=alice.id, subject_id=subject.id,
                score=85.0, semester="2026-S1",
            ),
        )
        crud.create_grade(
            db_session,
            schemas.GradeCreate(
                student_id=bob.id, subject_id=subject.id,
                score=70.0, semester="2026-S1",
            ),
        )
        alice_grades = crud.list_grades(db_session, student_id=alice.id)
        assert len(alice_grades) == 1
        assert alice_grades[0].score == 85.0

    def test_list_grades_filtered_by_semester(self, db_session):
        student = crud.create_student(
            db_session, schemas.StudentCreate(name="Alice", grade_level="5A")
        )
        subject = crud.create_subject(db_session, schemas.SubjectCreate(name="Math"))
        crud.create_grade(
            db_session,
            schemas.GradeCreate(
                student_id=student.id, subject_id=subject.id,
                score=85.0, semester="2026-S1",
            ),
        )
        crud.create_grade(
            db_session,
            schemas.GradeCreate(
                student_id=student.id, subject_id=subject.id,
                score=90.0, semester="2026-S2",
            ),
        )
        s1 = crud.list_grades(db_session, semester="2026-S1")
        assert len(s1) == 1
        assert s1[0].score == 85.0


# ---- Computed: student_summary -----------------------------------------

class TestStudentSummary:
    def test_summary_returns_none_for_unknown_student(self, db_session):
        assert crud.student_summary(db_session, 999) is None

    def test_summary_with_no_grades_returns_empty_subjects(self, db_session):
        student = crud.create_student(
            db_session, schemas.StudentCreate(name="Alice", grade_level="5A")
        )
        summary = crud.student_summary(db_session, student.id)
        assert summary is not None
        assert summary.student_id == student.id
        assert summary.student_name == "Alice"
        assert summary.subjects == []

    def test_summary_averages_grades_by_subject(self, db_session):
        student = crud.create_student(
            db_session, schemas.StudentCreate(name="Alice", grade_level="5A")
        )
        math = crud.create_subject(db_session, schemas.SubjectCreate(name="Math"))
        english = crud.create_subject(db_session, schemas.SubjectCreate(name="English"))

        # Two math grades: 80, 90 → average 85
        for score in (80.0, 90.0):
            crud.create_grade(
                db_session,
                schemas.GradeCreate(
                    student_id=student.id, subject_id=math.id,
                    score=score, semester="2026-S1",
                ),
            )
        # One English grade: 70
        crud.create_grade(
            db_session,
            schemas.GradeCreate(
                student_id=student.id, subject_id=english.id,
                score=70.0, semester="2026-S1",
            ),
        )

        summary = crud.student_summary(db_session, student.id)
        assert len(summary.subjects) == 2

        by_subject = {s.subject_name: s for s in summary.subjects}
        assert by_subject["Math"].average_score == 85.0
        assert by_subject["Math"].grade_count == 2
        assert by_subject["English"].average_score == 70.0
        assert by_subject["English"].grade_count == 1

    def test_summary_filtered_by_semester_only_counts_that_semester(self, db_session):
        student = crud.create_student(
            db_session, schemas.StudentCreate(name="Alice", grade_level="5A")
        )
        math = crud.create_subject(db_session, schemas.SubjectCreate(name="Math"))
        crud.create_grade(
            db_session,
            schemas.GradeCreate(
                student_id=student.id, subject_id=math.id,
                score=80.0, semester="2026-S1",
            ),
        )
        crud.create_grade(
            db_session,
            schemas.GradeCreate(
                student_id=student.id, subject_id=math.id,
                score=95.0, semester="2026-S2",
            ),
        )
        s1 = crud.student_summary(db_session, student.id, semester="2026-S1")
        assert len(s1.subjects) == 1
        assert s1.subjects[0].average_score == 80.0
        assert s1.subjects[0].grade_count == 1
