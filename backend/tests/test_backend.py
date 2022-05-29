import json

import pytest

from backend import create_app


@pytest.fixture()
def app():
    app = create_app()
    app.config.update({"TESTING": True})
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()


def test_init(client):
    response = client.post(
        "/parking/init", json={"entry_points": 3, "slots": [[1, 2, 3]], "sizes": [0]}
    )
    assert response.status_code == 201
    assert response.data.decode() == "System initialized"


def test_already_init(client):
    response = client.post(
        "/parking/init", json={"entry_points": 3, "slots": [[1, 2, 3]], "sizes": [0]}
    )
    assert response.status_code == 400
    assert response.data.decode() == "System already initialized"


def test_get_slots(client):
    response = client.get("/parking/slots")

    data = json.loads(response.data.decode())
    assert len(data["slots"]) == 1


def test_park(client):
    response = client.post(
        "parking/park",
        json={
            "plate_number": "ABC-123",
            "size": 0,
            "entry_point": 0,
            "time_parked": [2022, 5, 29, 0, 0],
        },
    )

    data = json.loads(response.data.decode())
    assert data["location"] == [1, 2, 3]


def test_get_vehicles(client):
    response = client.get("/parking/vehicles")

    data = json.loads(response.data.decode())
    assert len(data["vehicles"]) == 1


def test_alread_parked_error(client):
    response = client.post(
        "parking/park", json={"plate_number": "ABC-123", "size": 0, "entry_point": 0}
    )

    assert response.status_code == 400
    assert response.data.decode() == "Vehicle already parked."


def test_no_slot_available_error(client):
    response = client.post(
        "parking/park", json={"plate_number": "BCD-234", "size": 0, "entry_point": 0}
    )

    assert response.status_code == 503
    assert response.data.decode() == "No slots available."


def test_invalid_entry_point_error(client):
    response = client.post(
        "parking/park", json={"plate_number": "BCD-234", "size": 1, "entry_point": 4}
    )

    assert response.status_code == 400
    assert response.data.decode() == "Invalid entry point."


def test_unpark(client):
    response = client.post(
        "parking/unpark",
        json={"plate_number": "ABC-123", "time_unparked": [2022, 5, 29, 20, 30]},
    )

    data = json.loads(response.data.decode())
    assert data["charge"] == 400


def test_unpark_error(client):
    response = client.post("parking/unpark", json={"plate_number": "BCD-234"})

    assert response.status_code == 400
    assert response.data.decode() == "Vehicle not parked."
