"""
Tests for the Mergington High School API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)

@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    from app import activities
    
    # Store original state
    original_state = {
        name: {
            "description": activity["description"],
            "schedule": activity["schedule"],
            "max_participants": activity["max_participants"],
            "participants": activity["participants"].copy()
        }
        for name, activity in activities.items()
    }
    
    yield
    
    # Restore original state
    for name, activity in activities.items():
        activity["participants"] = original_state[name]["participants"].copy()


class TestRoot:
    """Test root endpoint"""
    
    def test_root_redirects_to_static(self, client):
        """Test that root endpoint redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestActivities:
    """Test activities endpoints"""
    
    def test_get_activities(self, client):
        """Test getting all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        activities = response.json()
        
        # Verify expected activities exist
        expected_activities = [
            "Basketball Team",
            "Soccer Club",
            "Art Club",
            "Drama Society",
            "Mathletes",
            "Debate Club",
            "Chess Club",
            "Programming Class",
            "Gym Class"
        ]
        
        for activity in expected_activities:
            assert activity in activities
            assert "description" in activities[activity]
            assert "schedule" in activities[activity]
            assert "max_participants" in activities[activity]
            assert "participants" in activities[activity]
    
    def test_activities_have_correct_structure(self, client):
        """Test that each activity has the correct structure"""
        response = client.get("/activities")
        activities = response.json()
        
        for name, activity in activities.items():
            assert isinstance(activity, dict)
            assert "description" in activity
            assert "schedule" in activity
            assert "max_participants" in activity
            assert "participants" in activity
            assert isinstance(activity["participants"], list)
            assert isinstance(activity["max_participants"], int)


class TestSignup:
    """Test signup endpoint"""
    
    def test_signup_for_activity(self, client, reset_activities):
        """Test signing up for an activity"""
        response = client.post(
            "/activities/Basketball Team/signup",
            params={"email": "test@example.com"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "test@example.com" in data["message"]
        assert "Basketball Team" in data["message"]
    
    def test_signup_adds_participant(self, client, reset_activities):
        """Test that signup actually adds the participant"""
        email = "student@mergington.edu"
        response = client.post(
            "/activities/Soccer Club/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities["Soccer Club"]["participants"]
    
    def test_signup_nonexistent_activity(self, client):
        """Test signing up for a non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": "test@example.com"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_signup_duplicate(self, client, reset_activities):
        """Test that duplicate signup is rejected"""
        email = "duplicate@example.com"
        
        # First signup should succeed
        response1 = client.post(
            "/activities/Art Club/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(
            "/activities/Art Club/signup",
            params={"email": email}
        )
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"].lower()
    
    def test_signup_with_existing_participants(self, client, reset_activities):
        """Test signup for an activity that already has participants"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "new@mergington.edu"}
        )
        assert response.status_code == 200
        
        # Verify both old and new participants exist
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert "michael@mergington.edu" in activities["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in activities["Chess Club"]["participants"]
        assert "new@mergington.edu" in activities["Chess Club"]["participants"]
