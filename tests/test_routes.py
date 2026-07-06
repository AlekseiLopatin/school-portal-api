"""
Integration tests for API routes — exercise the full stack:
HTTP → router → dependency injection → crud → DB → JSON response.

These use the `client` fixture from conftest.py, which is a FastAPI TestClient
running the real app in-process with an isolated test database. No real
network, no Uvicorn — but everything between routing and the DB is exercised
end-to-end, including Pydantic request/response validation and status codes.

Test classes are grouped by route. Each test name reads as a sentence describing
one specific behaviour of the API.
"""


# ---- Students -----------------------------------------------------------

class TestStudentsRoutes:
    def test_get_students_returns_empty_list_initially(self, client):
        response = client.get("/students")
        assert response.status_code == 200
        assert response.json() == []

    def test_post_student_creates_and_returns_201(self, client):
        response = client.post(
            "/students", json={"name": "Alice", "grade_level": "5A"}
        )
        assert response.status_code == 201
        body = response.json()
        assert body["name"] == "Alice"
        assert body["grade_level"] == "5A"
        assert "id" in body

    def test_post_student_rejects_empty_name(self, client):
        # Pydantic validation: name has min_length=1 in schemas.py
        response = client.post("/students", json={"name": "", "grade_level": "5A"})
        assert response.status_code == 422

    def test_post_student_rejects_missing_grade_level(self, client):
        response = client.post("/students", json={"name": "Alice"})
        assert response.status_code == 422

    def test_get_students_returns_all_created_students(self, client):
        client.post("/students", json={"name": "Alice", "grade_level": "5A"})
        client.post("/students", json={"name": "Bob", "grade_level": "5B"})
        response = client.get("/students")
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_get_student_by_id_returns_the_student(self, client):
        created = client.post(
            "/students", json={"name": "Alice", "grade_level": "5A"}
        ).json()
        response = client.get(f"/students/{created['id']}")
        assert response.status_code == 200
        assert response.json()["name"] == "Alice"

    def test_get_student_by_id_returns_404_when_not_found(self, client):
        response = client.get("/students/999")
        assert response.status_code == 404

    def test_patch_student_updates_only_sent_fields(self, client):
        created = client.post(
            "/students", json={"name": "Alice", "grade_level": "5A"}
        ).json()
        # Send only grade_level; name should stay "Alice"
        response = client.patch(
            f"/students/{created['id']}", json={"grade_level": "5B"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["name"] == "Alice"
        assert body["grade_level"] == "5B"

    def test_patch_student_returns_404_when_not_found(self, client):
        response = client.patch("/students/999", json={"name": "Ghost"})
        assert response.status_code == 404

    def test_delete_student_returns_204_and_removes_it(self, client):
        created = client.post(
            "/students", json={"name": "Alice", "grade_level": "5A"}
        ).json()
        response = client.delete(f"/students/{created['id']}")
        assert response.status_code == 204
        # And the student is actually gone
        assert client.get(f"/students/{created['id']}").status_code == 404

    def test_delete_student_returns_404_when_not_found(self, client):
        response = client.delete("/students/999")
        assert response.status_code == 404

    def test_student_summary_returns_404_for_unknown_student(self, client):
        response = client.get("/students/999/summary")
        assert response.status_code == 404

    def test_student_summary_returns_empty_subjects_for_new_student(self, client):
        created = client.post(
            "/students", json={"name": "Alice", "grade_level": "5A"}
        ).json()
        response = client.get(f"/students/{created['id']}/summary")
        assert response.status_code == 200
        body = response.json()
        assert body["student_name"] == "Alice"
        assert body["subjects"] == []


# ---- Subjects -----------------------------------------------------------

class TestSubjectsRoutes:
    def test_get_subjects_returns_empty_list_initially(self, client):
        response = client.get("/subjects")
        assert response.status_code == 200
        assert response.json() == []

    def test_post_subject_creates_and_returns_201(self, client):
        response = client.post("/subjects", json={"name": "Math"})
        assert response.status_code == 201
        assert response.json()["name"] == "Math"

    def test_post_subject_rejects_empty_name(self, client):
        response = client.post("/subjects", json={"name": ""})
        assert response.status_code == 422

    def test_get_subjects_returns_all_created(self, client):
        client.post("/subjects", json={"name": "Math"})
        client.post("/subjects", json={"name": "English"})
        response = client.get("/subjects")
        assert len(response.json()) == 2


# ---- Grades -------------------------------------------------------------

class TestGradesRoutes:
    """Each test creates its own student + subject through the API."""

    @staticmethod
    def _make_student_and_subject(client):
        student = client.post(
            "/students", json={"name": "Alice", "grade_level": "5A"}
        ).json()
        subject = client.post("/subjects", json={"name": "Math"}).json()
        return student["id"], subject["id"]

    def test_post_grade_creates_and_returns_201(self, client):
        student_id, subject_id = self._make_student_and_subject(client)
        response = client.post(
            "/grades",
            json={
                "student_id": student_id,
                "subject_id": subject_id,
                "score": 85.0,
                "semester": "2026-S1",
            },
        )
        assert response.status_code == 201
        body = response.json()
        assert body["score"] == 85.0
        assert "id" in body

    def test_post_grade_rejects_score_above_100(self, client):
        # Pydantic validation: score has le=100.0
        student_id, subject_id = self._make_student_and_subject(client)
        response = client.post(
            "/grades",
            json={
                "student_id": student_id,
                "subject_id": subject_id,
                "score": 105.0,
                "semester": "2026-S1",
            },
        )
        assert response.status_code == 422

    def test_get_grades_no_filters_returns_all(self, client):
        student_id, subject_id = self._make_student_and_subject(client)
        for score in (85.0, 90.0):
            client.post(
                "/grades",
                json={
                    "student_id": student_id,
                    "subject_id": subject_id,
                    "score": score,
                    "semester": "2026-S1",
                },
            )
        response = client.get("/grades")
        assert len(response.json()) == 2

    def test_get_grades_filtered_by_student(self, client):
        alice = client.post(
            "/students", json={"name": "Alice", "grade_level": "5A"}
        ).json()
        bob = client.post(
            "/students", json={"name": "Bob", "grade_level": "5B"}
        ).json()
        subject = client.post("/subjects", json={"name": "Math"}).json()
        client.post(
            "/grades",
            json={
                "student_id": alice["id"], "subject_id": subject["id"],
                "score": 85.0, "semester": "2026-S1",
            },
        )
        client.post(
            "/grades",
            json={
                "student_id": bob["id"], "subject_id": subject["id"],
                "score": 70.0, "semester": "2026-S1",
            },
        )
        response = client.get(f"/grades?student_id={alice['id']}")
        assert len(response.json()) == 1
        assert response.json()[0]["score"] == 85.0


# ---- End-to-end flow ----------------------------------------------------

class TestEndToEndFlow:
    """One test that walks through the full real-world flow."""

    def test_create_student_subject_grades_then_check_summary(self, client):
        student = client.post(
            "/students", json={"name": "Alice", "grade_level": "5A"}
        ).json()
        math = client.post("/subjects", json={"name": "Math"}).json()

        # Record two math grades for Alice
        for score in (80.0, 90.0):
            client.post(
                "/grades",
                json={
                    "student_id": student["id"],
                    "subject_id": math["id"],
                    "score": score,
                    "semester": "2026-S1",
                },
            )

        # Summary should show one subject (Math) with average 85, two grades
        summary = client.get(f"/students/{student['id']}/summary").json()
        assert summary["student_name"] == "Alice"
        assert len(summary["subjects"]) == 1
        assert summary["subjects"][0]["subject_name"] == "Math"
        assert summary["subjects"][0]["average_score"] == 85.0
        assert summary["subjects"][0]["grade_count"] == 2
