"""
Test suite for FastAPI activity signup endpoints.
Uses Arrange-Act-Assert (AAA) pattern for each test.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        # Arrange
        expected_activities = ["Chess Club", "Programming Class", "Gym Class"]
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all(activity in data for activity in expected_activities)

    def test_get_activities_includes_correct_fields(self, client):
        # Arrange
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        for activity in data.values():
            assert all(field in activity for field in required_fields)

    def test_get_activities_shows_correct_participant_count(self, client):
        # Arrange
        activity_name = "Chess Club"
        expected_participant_count = 2
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data[activity_name]["participants"]) == expected_participant_count


class TestRootRedirect:
    """Tests for GET / endpoint"""

    def test_root_redirects_to_static_index(self, client):
        # Arrange
        expected_redirect_url = "/static/index.html"
        
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == expected_redirect_url


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_successful_for_valid_activity_and_email(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert email in data["message"]

    def test_signup_adds_participant_to_activity(self, client):
        # Arrange
        activity_name = "Programming Class"
        email = "newstudent@mergington.edu"
        expected_initial_count = 2
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 200
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert len(activities_data[activity_name]["participants"]) == expected_initial_count + 1
        assert email in activities_data[activity_name]["participants"]

    def test_signup_rejects_duplicate_participant(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"].lower()

    def test_signup_rejects_nonexistent_activity(self, client):
        # Arrange
        activity_name = "Nonexistent Club"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_signup_with_special_characters_in_activity_name(self, client):
        # Arrange
        activity_name = "Gym Class"
        email = "athlete@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/signup endpoint"""

    def test_unregister_successful_for_registered_student(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already registered
        expected_initial_count = 2
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        assert email in data["message"]

    def test_unregister_removes_participant_from_activity(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        expected_initial_count = 2
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 200
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert len(activities_data[activity_name]["participants"]) == expected_initial_count - 1
        assert email not in activities_data[activity_name]["participants"]

    def test_unregister_rejects_nonregistered_student(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "unregistered@mergington.edu"  # Not signed up
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"].lower()

    def test_unregister_rejects_nonexistent_activity(self, client):
        # Arrange
        activity_name = "Nonexistent Club"
        email = "student@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_unregister_allows_student_to_signup_again(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "student@mergington.edu"
        
        # Act - Sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # Unregister
        unregister_response = client.delete(
            f"/activities/{activity_name}/signup?email={email}"
        )
        assert unregister_response.status_code == 200
        
        # Sign up again
        signup_again_response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert signup_again_response.status_code == 200
