import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

# Import your FastAPI app
from app.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "The RAG API is running smoothly.",
        "documentation_url": "/docs"
    }


def test_get_metadata():
    response = client.get("/metadata")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_upload_invalid_file_type():
    # Create a dummy text file
    files = {"files": ("test.txt", b"This is a text file, not a PDF.", "text/plain")}

    response = client.post("/upload", files=files)

    # Should return 400 Bad Request based on your routes.py logic
    assert response.status_code == 400
    assert "not a PDF" in response.json()["detail"]


def test_upload_too_many_files():
    # Create 21 dummy PDF files
    files = [("files", (f"file_{i}.pdf", b"%PDF-1.4 dummy content", "application/pdf")) for i in range(21)]

    response = client.post("/upload", files=files)

    assert response.status_code == 400
    assert "up to 20 documents" in response.json()["detail"]

def test_query_validation_error():
    # Missing the 'question' field
    response = client.post("/query", json={"thread_id": "12345"})
    assert response.status_code == 422


@patch("app.api.routes.graph_app.invoke")
def test_query_success_mocked(mock_invoke):
    expected_answer = "This is a simulated answer from the RAG pipeline."
    mock_invoke.return_value = {"answer": expected_answer}

    payload = {
        "question": "What is the capital of France?",
        "thread_id": "test-session-999"
    }

    response = client.post("/query", json=payload)

    assert response.status_code == 200
    data = response.json()

    assert "answer" in data
    assert data["answer"] == expected_answer
    assert data["thread_id"] == "test-session-999"

    mock_invoke.assert_called_once()
    args, kwargs = mock_invoke.call_args
    assert args[0]["question"] == "What is the capital of France?"
    assert kwargs["config"]["configurable"]["thread_id"] == "test-session-999"