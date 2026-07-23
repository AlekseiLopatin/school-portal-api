"""
Auth tests: login flow, and that write routes actually enforce the JWT.

Uses the `test_user` / `test_credentials` / `auth_headers` fixtures from
conftest.py — a real user is seeded into the test DB and a real token is
issued via /auth/login, so this exercises the whole path (hash verify ->
token issue -> token decode -> dependency injection), not just isolated units.
"""


class TestLogin:
    def test_login_with_correct_credentials_returns_token(
        self, client, test_user, test_credentials
    ):
        response = client.post("/auth/login", data=test_credentials)
        assert response.status_code == 200
        body = response.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    def test_login_with_wrong_password_returns_401(
        self, client, test_user, test_credentials
    ):
        response = client.post(
            "/auth/login",
            data={"username": test_credentials["username"], "password": "wrong-password"},
        )
        assert response.status_code == 401

    def test_login_with_unknown_username_returns_401(self, client):
        response = client.post(
            "/auth/login",
            data={"username": "nobody", "password": "whatever123"},
        )
        assert response.status_code == 401


class TestProtectedRoutesRejectWithoutToken:
    """Every write route should 401 with no Authorization header at all."""

    def test_post_student_without_token_returns_401(self, client):
        response = client.post(
            "/students", json={"name": "Alice", "grade_level": "5A"}
        )
        assert response.status_code == 401

    def test_patch_student_without_token_returns_401(self, client):
        response = client.patch("/students/1", json={"name": "Ghost"})
        assert response.status_code == 401

    def test_delete_student_without_token_returns_401(self, client):
        response = client.delete("/students/1")
        assert response.status_code == 401

    def test_post_subject_without_token_returns_401(self, client):
        response = client.post("/subjects", json={"name": "Math"})
        assert response.status_code == 401

    def test_post_grade_without_token_returns_401(self, client):
        response = client.post(
            "/grades",
            json={
                "student_id": 1,
                "subject_id": 1,
                "score": 85.0,
                "semester": "2026-S1",
            },
        )
        assert response.status_code == 401


class TestProtectedRoutesRejectInvalidToken:
    def test_post_student_with_garbage_token_returns_401(self, client):
        response = client.post(
            "/students",
            json={"name": "Alice", "grade_level": "5A"},
            headers={"Authorization": "Bearer not-a-real-token"},
        )
        assert response.status_code == 401


class TestReadRoutesStayPublic:
    """GET routes should never require a token."""

    def test_get_students_without_token_returns_200(self, client):
        assert client.get("/students").status_code == 200

    def test_get_subjects_without_token_returns_200(self, client):
        assert client.get("/subjects").status_code == 200

    def test_get_grades_without_token_returns_200(self, client):
        assert client.get("/grades").status_code == 200


class TestProtectedRoutesAcceptValidToken:
    def test_post_student_with_valid_token_succeeds(self, client, auth_headers):
        response = client.post(
            "/students",
            json={"name": "Alice", "grade_level": "5A"},
            headers=auth_headers,
        )
        assert response.status_code == 201

    def test_post_subject_with_valid_token_succeeds(self, client, auth_headers):
        response = client.post(
            "/subjects", json={"name": "Math"}, headers=auth_headers
        )
        assert response.status_code == 201

    def test_full_write_flow_with_valid_token_succeeds(self, client, auth_headers):
        student = client.post(
            "/students",
            json={"name": "Alice", "grade_level": "5A"},
            headers=auth_headers,
        ).json()
        subject = client.post(
            "/subjects", json={"name": "Math"}, headers=auth_headers
        ).json()
        grade_response = client.post(
            "/grades",
            json={
                "student_id": student["id"],
                "subject_id": subject["id"],
                "score": 90.0,
                "semester": "2026-S1",
            },
            headers=auth_headers,
        )
        assert grade_response.status_code == 201

        update_response = client.patch(
            f"/students/{student['id']}",
            json={"grade_level": "5B"},
            headers=auth_headers,
        )
        assert update_response.status_code == 200

        delete_response = client.delete(
            f"/students/{student['id']}", headers=auth_headers
        )
        assert delete_response.status_code == 204
