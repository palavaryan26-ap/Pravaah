"""API tests for the Pravaah framework."""

def test_health_check(client):
    """Test the core health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert "plugins_loaded" in data


def test_ai_endpoints(client):
    """Test the AI core endpoints with the mock provider."""
    # Test /ai/complete
    response = client.post("/ai/complete", json={"prompt": "Hello"})
    assert response.status_code == 200
    assert "content" in response.json()

    # Test /ai/summarize
    response = client.post("/ai/summarize", json={"text": "A long text"})
    assert response.status_code == 200
    assert "summary" in response.json()

    # Test /ai/extract
    response = client.post("/ai/extract", json={
        "text": "My name is John", 
        "schema": {"name": "string"}
    })
    assert response.status_code == 200
