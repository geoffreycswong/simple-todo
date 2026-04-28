import os
import pytest
from fastapi.testclient import TestClient

def test_serve_static_index(client):
    # This test assumes frontend/dist/index.html exists for the purpose of testing the mounting logic
    # In the test environment, we might need to mock or create a dummy file
    static_dir = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
    os.makedirs(static_dir, exist_ok=True)
    index_file = os.path.join(static_dir, "index.html")
    with open(index_file, "w") as f:
        f.write("<html><body>Hello World</body></html>")
    
    # We need to re-import the app or ensure the mounting logic is executed
    # Since we are using the 'client' fixture from conftest, which imports 'app'
    # we might need to be careful.
    
    response = client.get("/")
    # If not implemented, this might return 404 or something else
    # Actually, FastAPI might have a default behavior for / if not defined.
    # In our main.py, there is no route for /
    
    assert response.status_code == 200
    assert "Hello World" in response.text
