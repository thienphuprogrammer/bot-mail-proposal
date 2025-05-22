import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.core.config import settings
import mongomock
from datetime import datetime, timedelta
import jwt
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
backend_dir = Path(__file__).parent.parent
src_dir = backend_dir / "src"
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(src_dir))

@pytest.fixture(scope="session")
def client():
    """Test client fixture"""
    return TestClient(app)

@pytest.fixture(scope="session")
def mock_mongo():
    """Mock MongoDB fixture"""
    return mongomock.MongoClient()

@pytest.fixture(scope="session")
def test_token():
    """Generate a test JWT token"""
    token_data = {
        "sub": "testuser",
        "exp": datetime.utcnow() + timedelta(minutes=15)
    }
    return jwt.encode(token_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

@pytest.fixture(scope="session")
def auth_headers(test_token):
    """Headers with authentication token"""
    return {"Authorization": f"Bearer {test_token}"}

@pytest.fixture(scope="session")
def test_template():
    """Test template data"""
    return {
        "name": "Test Template",
        "content": "This is a test template content",
        "description": "Test template description"
    }

@pytest.fixture(scope="session")
def test_proposal():
    """Test proposal data"""
    return {
        "project_name": "Test Project",
        "description": "Test project description",
        "status": "draft"
    }

@pytest.fixture(scope="session")
def test_email():
    """Test email data"""
    return {
        "subject": "Test Email",
        "body": "This is a test email body",
        "sender": "sender@example.com",
        "recipient": "recipient@example.com",
        "processed": False
    }

@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment variables"""
    os.environ["TESTING"] = "true"
    os.environ["MONGODB_URL"] = "mongodb://localhost:27017/test_db"
    yield
    os.environ.pop("TESTING", None)
    os.environ.pop("MONGODB_URL", None) 