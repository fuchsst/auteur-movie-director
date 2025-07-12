"""
Tests for main FastAPI application.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "docs" in data


def test_health_endpoint():
    """Test health check endpoint"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded", "unhealthy"]
    assert "timestamp" in data
    assert "service" in data
    assert "version" in data
    assert "checks" in data
    assert "api" in data["checks"]
    assert "redis" in data["checks"]
    assert "workspace" in data["checks"]


def test_info_endpoint():
    """Test API info endpoint"""
    response = client.get("/api/v1/info")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "environment" in data
    assert "quality_presets" in data
    assert "default_quality" in data
    assert "features" in data

    # Check features
    features = data["features"]
    assert features["websocket"] is True
    assert features["task_dispatcher"] is True
    assert features["redis_pubsub"] is True
    assert "crew_ai" in features


def test_cors_headers():
    """Test CORS headers are present"""
    # Test CORS headers on actual request (OPTIONS may not be implemented)
    response = client.get("/api/v1/health", headers={"Origin": "http://localhost:3000"})
    
    # Check for CORS headers (case-insensitive)
    headers_lower = {k.lower(): v for k, v in response.headers.items()}
    assert "access-control-allow-origin" in headers_lower
    assert "access-control-allow-credentials" in headers_lower
    assert "access-control-expose-headers" in headers_lower
    
    # Verify the values
    assert headers_lower["access-control-allow-origin"] == "http://localhost:3000"
    assert headers_lower["access-control-allow-credentials"] == "true"


def test_request_id_header():
    """Test request ID is added to responses"""
    response = client.get("/api/v1/health")
    assert "x-request-id" in response.headers


def test_404_error_format():
    """Test 404 error response format"""
    response = client.get("/api/v1/nonexistent")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert "code" in data["error"]
    assert "message" in data["error"]
    assert "request_id" in data
    assert "timestamp" in data


def test_validation_error_format():
    """Test validation error response format"""
    # Try to create project with invalid data
    response = client.post("/api/v1/workspace/projects", json={})
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "details" in data["error"]
    assert "errors" in data["error"]["details"]
