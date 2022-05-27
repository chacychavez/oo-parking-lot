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
    assert False


def test_park_error(client):
    assert False


def test_unpark(client):
    assert False


def test_unpark_error(client):
    assert False
