import pytest
from fastapi.testclient import TestClient
from src.main import app
from datetime import datetime
from bson import ObjectId

client = TestClient(app)

def test_list_emails():
    """Test listing emails"""
    response = client.get("/api/v1/emails/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_list_emails_with_filters():
    """Test listing emails with filters"""
    # Test showing only processed emails
    response = client.get("/api/v1/emails/?show_processed=true&show_unprocessed=false")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    
    # Test showing only unprocessed emails
    response = client.get("/api/v1/emails/?show_processed=false&show_unprocessed=true")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_email_not_found():
    """Test getting a non-existent email"""
    non_existent_id = str(ObjectId())
    response = client.get(f"/api/v1/emails/{non_existent_id}")
    assert response.status_code == 404
    assert "Email not found" in response.json()["detail"]

def test_sync_emails():
    """Test syncing emails"""
    response = client.post(
        "/api/v1/emails/sync",
        params={
            "query": "isRead eq false",
            "max_results": 10,
            "folder": "inbox",
            "include_spam_trash": False,
            "only_recent": True
        }
    )
    assert response.status_code == 200
    assert isinstance(response.json(), dict)

def test_process_email_not_found():
    """Test processing a non-existent email"""
    non_existent_id = str(ObjectId())
    response = client.post(f"/api/v1/emails/{non_existent_id}/process")
    assert response.status_code == 404
    assert "Email not found" in response.json()["detail"]

def test_get_email_stats():
    """Test getting email statistics"""
    response = client.get("/api/v1/emails/stats/summary")
    assert response.status_code == 200
    stats = response.json()
    assert "total_emails" in stats
    assert "unprocessed_emails" in stats
    assert isinstance(stats["total_emails"], int)
    assert isinstance(stats["unprocessed_emails"], int) 