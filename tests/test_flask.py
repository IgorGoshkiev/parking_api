from datetime import datetime

import pytest
from parking_api.tests.factories import ClientFactory, ParkingFactory
from parking_api.main.models import Client, Parking


def test_create_client_factories(app, db):
    client = ClientFactory()
    db.session.commit()
    assert client.id is not None
    assert len(db.session.query(Client).all()) == 2


def test_create_parking_factories(app, db):
    parking = ParkingFactory()
    db.session.commit()
    assert parking.id is not None
    assert len(db.session.query(Parking).all()) == 2


@pytest.mark.parametrize("route", ["/parkings", "/client_parkings", "/clients/100",
                                   "/clients", "/"])
def test_route_status(client, route):
    rv = client.get(route)
    assert rv.status_code == 200


def test_client(client) -> None:
    resp = client.get("/clients/100")
    assert resp.status_code == 200
    assert resp.json == {"id": 100, "name": "name", "surname": "surname",
                         "credit_card": "1111 1111 1111 1111", "car_number": "L666XP"}


def test_parking(parking) -> None:
    resp = parking.get("/parkings")
    assert resp.status_code == 200
    assert resp.json == [{'address': 'address2',
                          'opened': True,
                          'count_available_places': 98,
                          'count_places': 100,
                          'id': 1}]


def test_create_client(client) -> None:
    client_data = {"name": "Ivan", "surname": "Ivanov",
                   "credit_card": "2222 1111 1111 2222", "car_number": "P555XP"}
    resp = client.post("/clients", data=client_data)
    assert resp.status_code == 201


def test_create_parking(parking) -> None:
    new_parking_zone = {"address": "address_new",
                        "opened": True,
                        "count_places": 500,
                        "count_available_places": 500}
    resp = parking.post("/parkings", data=new_parking_zone)
    assert resp.status_code == 201


def test_client_already_exists_parking(client_parking) -> None:
    client_parking_in_data = {"client_id": 100,
                              "parking_id": 1,
                              "time_in": datetime.strptime('2025-01-13 18:36:29', '%Y-%m-%d %H:%M:%S')}
    resp = client_parking.post("/client_parkings", data=client_parking_in_data)
    assert resp.status_code == 406


@pytest.mark.parking
def test_client_in_parking(client_parking) -> None:
    client_parking_in_data = {"client_id": 100,
                              "parking_id": 1,
                              "time_in": datetime.strptime('2025-01-13 18:36:29', '%Y-%m-%d %H:%M:%S'),
                              "time_out": datetime.now()}
    client_parking.delete("/client_parkings", data=client_parking_in_data)
    client_parking_in_data = {"client_id": 100,
                              "parking_id": 1,
                              "time_in": datetime.strptime('2025-01-13 18:36:29', '%Y-%m-%d %H:%M:%S')}
    resp = client_parking.post("/client_parkings", data=client_parking_in_data)
    assert resp.status_code == 201


@pytest.mark.parking
def test_client_out_parking(client_parking) -> None:
    client_parking_in_data = {"client_id": 100,
                              "parking_id": 1,
                              "time_in": datetime.strptime('2025-01-13 18:36:29', '%Y-%m-%d %H:%M:%S'),
                              "time_out": datetime.now()}
    resp = client_parking.delete("/client_parkings", data=client_parking_in_data)
    assert resp.status_code == 201


def test_app_config(app):
    assert not app.config['DEBUG']
    assert app.config['TESTING']
    assert app.config['SQLALCHEMY_DATABASE_URI'] == "sqlite://"
