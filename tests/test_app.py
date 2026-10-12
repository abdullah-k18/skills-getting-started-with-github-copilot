from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = deepcopy(activities)
    yield
    activities.clear()
    activities.update(original_activities)


@pytest.fixture
def client():
    return TestClient(app)


def test_root_redirects_to_static_index(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_activity_data(client):
    # Arrange
    activity_name = "Basketball Team"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json()[activity_name]["participants"] == []
    assert response.json()[activity_name]["max_participants"] == 15


def test_signup_adds_participant(client):
    # Arrange
    activity_name = "Basketball Team"
    email = "student@mergington.edu"

    # Act
    response = client.post(
        "/activities/Basketball%20Team/signup",
        params={"email": email},
    )
    activities_response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {activity_name}"
    }
    assert activities_response.json()[activity_name]["participants"] == [email]


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = client.post(
        "/activities/Chess%20Club/signup",
        params={"email": email},
    )
    activities_response = client.get("/activities")

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"
    participants = activities_response.json()[activity_name]["participants"]
    assert participants == [email, "daniel@mergington.edu"]


def test_signup_rejects_unknown_activity(client):
    # Arrange
    email = "student@mergington.edu"

    # Act
    response = client.post(
        "/activities/Unknown%20Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant_and_preserves_others(client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = client.delete(
        "/activities/Chess%20Club/signup",
        params={"email": email},
    )
    activities_response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from {activity_name}"
    }
    participants = activities_response.json()[activity_name]["participants"]
    assert participants == ["daniel@mergington.edu"]


def test_unregister_rejects_unknown_activity(client):
    # Arrange
    email = "student@mergington.edu"

    # Act
    response = client.delete(
        "/activities/Unknown%20Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_rejects_nonparticipant(client):
    # Arrange
    activity_name = "Basketball Team"
    email = "student@mergington.edu"

    # Act
    response = client.delete(
        "/activities/Basketball%20Team/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
    assert activities[activity_name]["participants"] == []