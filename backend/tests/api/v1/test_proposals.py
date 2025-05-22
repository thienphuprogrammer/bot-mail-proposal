import pytest
from fastapi.testclient import TestClient
from src.main import app
from datetime import datetime
from bson import ObjectId

client = TestClient(app)

def test_list_proposals():
    """Test listing proposals"""
    response = client.get("/api/v1/proposals/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_list_proposals_with_status():
    """Test listing proposals with status filter"""
    response = client.get("/api/v1/proposals/?status=draft")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_proposal_not_found():
    """Test getting a non-existent proposal"""
    non_existent_id = str(ObjectId())
    response = client.get(f"/api/v1/proposals/{non_existent_id}")
    assert response.status_code == 404
    assert "Proposal not found" in response.json()["detail"]

def test_generate_proposal_not_found():
    """Test generating a proposal for non-existent email"""
    non_existent_id = str(ObjectId())
    response = client.post(f"/api/v1/proposals/{non_existent_id}/generate")
    assert response.status_code == 404
    assert "Proposal not found" in response.json()["detail"]

def test_send_proposal_not_found():
    """Test sending a non-existent proposal"""
    non_existent_id = str(ObjectId())
    response = client.post(
        f"/api/v1/proposals/{non_existent_id}/send",
        params={"recipient_email": "test@example.com"}
    )
    assert response.status_code == 404
    assert "Proposal not found" in response.json()["detail"]

def test_get_proposal_stats():
    """Test getting proposal statistics"""
    response = client.get("/api/v1/proposals/stats/summary")
    assert response.status_code == 200
    stats = response.json()
    assert "total_proposals" in stats
    assert "status_counts" in stats
    assert isinstance(stats["total_proposals"], int)
    assert isinstance(stats["status_counts"], dict)

def test_approve_proposal_not_found():
    """Test approving a non-existent proposal"""
    non_existent_id = str(ObjectId())
    response = client.post(
        f"/api/v1/proposals/{non_existent_id}/approve",
        params={"approval_notes": "Test approval"}
    )
    assert response.status_code == 404
    assert "Proposal not found" in response.json()["detail"]

def test_generate_pdf_not_found():
    """Test generating PDF for non-existent proposal"""
    non_existent_id = str(ObjectId())
    response = client.post(f"/api/v1/proposals/{non_existent_id}/generate-pdf")
    assert response.status_code == 404
    assert "Proposal not found" in response.json()["detail"] 