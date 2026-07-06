"""
Smoke tests: verify the test infrastructure works before writing real tests.

If these two pass, the fixtures in conftest.py are wired correctly and we can
move on to actual unit + integration tests.
"""


def test_health_endpoint_returns_ok(client):
    """The /health endpoint is reachable and returns {"status": "ok"}."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_each_test_gets_a_fresh_empty_database(client):
    """
    Every test starts with an empty DB.
    If state leaked between tests, this would fail after the next test
    creates a student.
    """
    response = client.get("/students")
    assert response.status_code == 200
    assert response.json() == []
