"""
Integration tests for the Mergington High School Activities API.

Using the AAA (Arrange-Act-Assert) pattern:
- Arrange: Set up test data and conditions
- Act: Execute the API call
- Assert: Verify the response and side effects
"""

import pytest


class TestRootRedirect:
    """Test the root endpoint redirect behavior."""
    
    def test_root_redirects_to_static_index(self, client):
        """
        Test that GET / redirects to the static frontend.
        
        Arrange: Client is ready (from fixture)
        Act: Make GET request to root
        Assert: Verify redirect response to /static/index.html
        """
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Test the GET /activities endpoint."""
    
    def test_get_all_activities_returns_success(self, client):
        """
        Test that GET /activities returns all available activities.
        
        Arrange: Client is ready with 9 activities in the database
        Act: Make GET request to /activities
        Assert: Verify 200 status and all activities are returned
        """
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        activities = response.json()
        assert len(activities) == 9
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        assert "Gym Class" in activities
    
    def test_activity_contains_required_fields(self, client):
        """
        Test that each activity object has the required fields.
        
        Arrange: Client is ready
        Act: Make GET request to /activities
        Assert: Verify each activity contains description, schedule, max_participants, participants
        """
        # Act
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        for activity_name, activity_data in activities.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)
    
    def test_get_activities_includes_existing_participants(self, client):
        """
        Test that activities return the list of current participants.
        
        Arrange: Client is ready; Chess Club has 2 participants
        Act: Make GET request to /activities
        Assert: Verify Chess Club includes both participants
        """
        # Act
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        chess_club = activities["Chess Club"]
        assert len(chess_club["participants"]) == 2
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]


class TestSignupForActivity:
    """Test the POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_new_student_success(self, client):
        """
        Test successful signup of a new student to an activity.
        
        Arrange: Client ready; Programming Class has 2 participants initially
        Act: Sign up a new student to Programming Class
        Assert: Verify success response and participant count increased
        """
        # Arrange
        activity_name = "Programming Class"
        new_email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {new_email} for {activity_name}"
        
        # Verify participant was added by checking GET /activities
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert new_email in participants
        assert len(participants) == 3  # Was 2, now 3
    
    def test_signup_duplicate_email_fails(self, client):
        """
        Test that signing up with an already registered email fails.
        
        Arrange: Michael is already in Chess Club
        Act: Try to sign up Michael again to Chess Club
        Assert: Verify 400 error with appropriate message
        """
        # Arrange
        activity_name = "Chess Club"
        existing_email = "michael@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": existing_email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_nonexistent_activity_fails(self, client):
        """
        Test that signing up to a non-existent activity fails.
        
        Arrange: "Fake Club" does not exist
        Act: Try to sign up to "Fake Club"
        Assert: Verify 404 error with activity not found message
        """
        # Arrange
        fake_activity = "Fake Club"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{fake_activity}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]


class TestUnregisterFromActivity:
    """Test the DELETE /activities/{activity_name}/signup endpoint."""
    
    def test_unregister_existing_participant_success(self, client):
        """
        Test successful unregistration of an existing participant.
        
        Arrange: Michael is in Chess Club with 2 participants
        Act: Unregister Michael from Chess Club
        Assert: Verify success and participant removed from activity
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Removed {email} from {activity_name}"
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert email not in participants
        assert len(participants) == 1  # Was 2, now 1
    
    def test_unregister_nonexistent_participant_fails(self, client):
        """
        Test that unregistering a participant not in the activity fails.
        
        Arrange: Bob is not in Chess Club
        Act: Try to unregister Bob from Chess Club
        Assert: Verify 404 error with participant not found message
        """
        # Arrange
        activity_name = "Chess Club"
        absent_email = "bob@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": absent_email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "Participant not found" in response.json()["detail"]
    
    def test_unregister_from_nonexistent_activity_fails(self, client):
        """
        Test that unregistering from a non-existent activity fails.
        
        Arrange: "Fake Club" does not exist
        Act: Try to unregister from "Fake Club"
        Assert: Verify 404 error with activity not found message
        """
        # Arrange
        fake_activity = "Fake Club"
        email = "student@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{fake_activity}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
