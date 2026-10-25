
import os
import sys
import pytest

sys.path.insert(
    0, os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
)

import app as app_module


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Use a temporary database for testing
    test_db = tmp_path / "test_notenova.db"
    monkeypatch.setattr(app_module, "DATABASE", str(test_db))
    app_module.init_db()

    app_module.app.config["TESTING"] = True

    with app_module.app.test_client() as client:
        yield client


def test_homepage(client):
    response = client.get("/")
    assert response.status_code == 200


def test_analyze_page(client):
    response = client.get("/analyze")
    assert response.status_code == 200


def test_dashboard_page(client):
    response = client.get("/dashboard")
    assert response.status_code == 200


def test_text_analysis(client):
    response = client.post(
        "/analyze",
        data={
            "notes": (
                "Machine learning is a branch of artificial "
                "intelligence. It helps computers learn from data. "
                "Machine learning is used in many applications."
            )
        }
    )

    assert response.status_code == 200
    assert b"Machine learning" in response.data


def test_empty_notes(client):
    response = client.post(
        "/analyze",
        data={"notes": ""}
    )

    assert response.status_code == 200
    assert b"Please enter notes or upload a file." in response.data


def test_summary_generation():
    text = (
        "Python is a programming language. "
        "It is widely used for AI. "
        "Python is easy to learn."
    )

    summary = app_module.generate_summary(text)

    assert isinstance(summary, str)
    assert len(summary) > 0


def test_keyword_extraction():
    keywords = app_module.extract_keywords(
        "Python programming Python learning"
    )

    assert "python" in keywords


def test_quiz_generation():
    quiz = app_module.generate_quiz(
        "Python is used for programming. "
        "Machine learning uses data."
    )

    assert isinstance(quiz, list)
    assert len(quiz) > 0
