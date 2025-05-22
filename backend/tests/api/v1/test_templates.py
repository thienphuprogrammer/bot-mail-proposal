import pytest
from fastapi.testclient import TestClient
from src.main import app
from datetime import datetime
from bson import ObjectId

client = TestClient(app)

def test_list_templates():
    """Test listing templates"""
    response = client.get("/api/v1/templates/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_list_templates_with_status():
    """Test listing templates with status filter"""
    response = client.get("/api/v1/templates/?status=active")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_template_not_found():
    """Test getting a non-existent template"""
    non_existent_id = str(ObjectId())
    response = client.get(f"/api/v1/templates/{non_existent_id}")
    assert response.status_code == 404
    assert "Template not found" in response.json()["detail"]

def test_create_template():
    """Test creating a new template"""
    template_data = {
        "name": "Test Template",
        "content": "This is a test template content",
        "description": "Test template description"
    }
    response = client.post("/api/v1/templates/", json=template_data)
    assert response.status_code == 200
    assert "Template created successfully" in response.json()["message"]
    assert "template_id" in response.json()

def test_create_duplicate_template():
    """Test creating a template with duplicate name"""
    template_data = {
        "name": "Test Template",
        "content": "This is a test template content",
        "description": "Test template description"
    }
    # First creation
    client.post("/api/v1/templates/", json=template_data)
    
    # Try to create template with same name
    response = client.post("/api/v1/templates/", json=template_data)
    assert response.status_code == 400
    assert "Template with name" in response.json()["detail"]

def test_update_template_not_found():
    """Test updating a non-existent template"""
    non_existent_id = str(ObjectId())
    template_data = {
        "name": "Updated Template",
        "content": "Updated content",
        "description": "Updated description"
    }
    response = client.put(f"/api/v1/templates/{non_existent_id}", json=template_data)
    assert response.status_code == 404
    assert "Template not found" in response.json()["detail"]

def test_approve_template_not_found():
    """Test approving a non-existent template"""
    non_existent_id = str(ObjectId())
    response = client.post(f"/api/v1/templates/{non_existent_id}/approve")
    assert response.status_code == 404
    assert "Template not found" in response.json()["detail"]

def test_deactivate_template_not_found():
    """Test deactivating a non-existent template"""
    non_existent_id = str(ObjectId())
    response = client.post(f"/api/v1/templates/{non_existent_id}/deactivate")
    assert response.status_code == 404
    assert "Template not found" in response.json()["detail"]

def test_delete_template_not_found():
    """Test deleting a non-existent template"""
    non_existent_id = str(ObjectId())
    response = client.delete(f"/api/v1/templates/{non_existent_id}")
    assert response.status_code == 404
    assert "Template not found" in response.json()["detail"] 