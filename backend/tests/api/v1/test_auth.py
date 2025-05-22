import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.core.config import settings
import jwt
from datetime import datetime, timedelta

client = TestClient(app)

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_login_invalid_credentials():
    """Test login with invalid credentials"""
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "invalid", "password": "invalid"}
    )
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]

def test_register_user():
    """Test user registration"""
    test_user = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
        "full_name": "Test User"
    }
    response = client.post(
        "/api/v1/auth/register",
        params=test_user
    )
    assert response.status_code == 200
    assert "User registered successfully" in response.json()["message"]

def test_register_duplicate_user():
    """Test registering a duplicate user"""
    test_user = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
        "full_name": "Test User"
    }
    # First registration
    client.post("/api/v1/auth/register", params=test_user)
    
    # Try to register same user again
    response = client.post(
        "/api/v1/auth/register",
        params=test_user
    )
    assert response.status_code == 400
    assert "Username already registered" in response.json()["detail"]

def test_get_current_user():
    """Test getting current user info"""
    # Create test token
    token_data = {
        "sub": "testuser",
        "exp": datetime.utcnow() + timedelta(minutes=15)
    }
    token = jwt.encode(token_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["username"] == "testuser" 