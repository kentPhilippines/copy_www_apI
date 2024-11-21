from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Nginx Deploy API is running"

def test_nginx_status():
    response = client.get("/api/v1/nginx/status")
    assert response.status_code == 200 