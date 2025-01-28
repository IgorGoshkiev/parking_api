from datetime import datetime

import pytest
from parking_api.main.app import create_app
from parking_api.main.app import db as _db
from parking_api.main.models import Client, ClientParking, Parking


@pytest.fixture
def app():
    _app = create_app()
    _app.config["TESTING"] = True
    _app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"

    with _app.app_context():
        _db.create_all()
        client = Client(
            id=100,
            name="name",
            surname="surname",
            credit_card="1111 1111 1111 1111",
            car_number="L666XP",
        )
        parking = Parking(
            address="address2", opened=True, count_available_places=98, count_places=100
        )
        client_parking = ClientParking(
            client_id=100,
            parking_id=1,
            time_in=datetime.strptime("2025-01-13 18:36:29", "%Y-%m-%d %H:%M:%S"),
            time_out=None,
        )
        _db.session.add(client)
        _db.session.add(parking)
        _db.session.add(client_parking)
        _db.session.commit()

        yield _app
        _db.session.close()
        _db.drop_all()


@pytest.fixture
def client(app):
    client = app.test_client()
    yield client


@pytest.fixture
def parking(app):
    parking = app.test_client()
    yield parking


@pytest.fixture()
def client_parking(app):
    client_parking = app.test_client()
    yield client_parking


@pytest.fixture
def db(app):
    with app.app_context():
        yield _db
