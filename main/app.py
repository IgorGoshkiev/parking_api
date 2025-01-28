import datetime
from typing import List

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event, null

db = SQLAlchemy()


def create_app():
    from models import Client, ClientParking, Parking

    app = Flask(__name__, instance_relative_config=True)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///barrier.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    @app.before_request
    def before_request_func():
        db.create_all()

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()

    @app.route("/parkings", methods=["GET"])
    def get_prking():
        """get pargings"""
        parkings: List[Parking] = db.session.query(Parking).all()
        parkings_list = [u.to_json() for u in parkings]
        return jsonify(parkings_list), 200

    @app.route("/clients", methods=["GET"])
    def get_clients():
        """Получение клиентов"""
        clients: List[Client] = db.session.query(Client).all()
        clients_list = [u.to_json() for u in clients]
        return jsonify(clients_list), 200

    @app.route("/clients/<int:client_id>", methods=["GET"])
    def get_client(client_id: int):
        client: Client = db.session.query(Client).get(client_id)
        return jsonify(client.to_json()), 200

    @app.route("/clients", methods=["POST"])
    def create_client():
        name = request.form.get("name", type=str)
        surname = request.form.get("surname", type=str)
        credit_card = request.form.get("credit_card", type=int)
        car_number = request.form.get("car_number", type=str)

        new_client = Client(
            name=name, surname=surname, credit_card=credit_card,
            car_number=car_number
        )

        db.session.add(new_client)
        db.session.commit()
        return "", 201

    @app.route("/parkings", methods=["POST"])
    def create_parking_zone():
        address = request.form.get("address", type=str)
        opened = request.form.get("opened", type=bool)
        count_places = request.form.get("count_places", type=int)
        count_available_places = request.form.get("count_available_places",
                                                  type=int)

        new_parking_zone = Parking(
            address=address,
            opened=opened,
            count_places=count_places,
            count_available_places=count_available_places,
        )

        db.session.add(new_parking_zone)
        db.session.commit()
        return "", 201

    @event.listens_for(Parking, "before_update")
    def check_open_status(mapper, connection, target):
        if target.count_available_places <= 0:
            target.opened = False
        else:
            target.opened = True

    @app.route("/client_parkings", methods=["POST"])
    def client_parking():
        parking_id = request.form.get("parking_id", type=int)
        query_parking_id = (
            db.session.query(Parking).filter(Parking.id == parking_id).first()
        )
        if not query_parking_id:
            return (
                jsonify(
                    {
                        "message": "Нет такой парковки,"
                                   " поробуйте ввести корректный адресс"
                    }
                ),
                404,
            )

        client_id = request.form.get("client_id", type=int)
        check_client_id = (
            db.session.query(Client).filter(Client.id == client_id).first()
        )
        if not check_client_id:
            return (
                jsonify({"message": "Такой клиент не найден, пройдите регистрацию"}),
                405,
            )

        all_visits_client_for_parking = (
            db.session.query(ClientParking)
            .filter(ClientParking.client_id == client_id)
            .all()
        )
        last_visit = all_visits_client_for_parking[-1]

        if last_visit:
            client_time_out = last_visit.time_out
            if client_time_out is None:
                return (
                    jsonify(
                        {"message": "Такой клиент уже запарковаля и еще не выехал"}
                    ),
                    406,
                )

        parking_available_places = query_parking_id.get_available_places()
        current_condition_parking = db.session.query(Parking).get(parking_id)

        if parking_available_places < 0:
            current_condition_parking.opened = False
            return jsonify({"message": "Нет свободных мест на парковке"}), 407

        else:
            parking_available_places -= 1
            current_condition_parking.count_available_places = parking_available_places
            current_condition_parking.opened = True

            add_client_for_parking = ClientParking(
                client_id=client_id,
                parking_id=parking_id,
                time_in=datetime.datetime.now(),
            )

            db.session.add_all([current_condition_parking, add_client_for_parking])
            db.session.commit()

            return "", 201

    @app.route("/client_parkings", methods=["DELETE"])
    def delete_client_parking():
        parking_id = request.form.get("parking_id", type=int)
        query_parking_id = (
            db.session.query(Parking).filter(Parking.id == parking_id).first()
        )
        if not query_parking_id:
            return (
                jsonify(
                    {
                        "message": "Нет такой парковки, "
                                   "поробуйте ввести корректный адресс"
                    }
                ),
                404,
            )

        client_id = request.form.get("client_id", type=int)
        check_client_id = (
            db.session.query(Client).filter(Client.id == client_id).first()
        )
        if not check_client_id:
            return (
                jsonify({"message": "Такой клиент не найден, пройдите регистрацию"}),
                405,
            )
        cards = (
            db.session.query(Client.credit_card).filter(Client.id == client_id).all()
        )
        check_card = cards[-1]
        if not check_card:
            return jsonify({"message": "Отсутсвует карта для оплаты парковки"}), 406

        all_visits_client_for_parking = (
            db.session.query(ClientParking)
            .filter(ClientParking.client_id == client_id)
            .all()
        )
        last_visit = all_visits_client_for_parking[-1]
        client_time_in = last_visit.time_in
        client_time_out = last_visit.time_out
        if client_time_out is None:
            client_time_out = datetime.datetime.now()
            string_date_time_in = client_time_out.strftime("%c")
            string_date_time_out = client_time_in.strftime("%c")
            if string_date_time_in < string_date_time_out:
                return (
                    jsonify(
                        {"message": "Время выезда не может быть меньше времени заезда"}
                    ),
                    407,
                )
            add_client_for_parking = ClientParking(
                client_id=client_id,
                parking_id=parking_id,
                time_in=client_time_in,
                time_out=client_time_out,
            )

            parking_available_places = query_parking_id.get_available_places()
            current_condition_parking = db.session.query(Parking).get(parking_id)
            parking_available_places += 1
            current_condition_parking.count_available_places = parking_available_places
            current_condition_parking.opened = True

            db.session.add_all([current_condition_parking, add_client_for_parking])
            db.session.commit()
            return "", 201

        else:
            return jsonify({"message": "Такой клиент уже давно выехал"}), 410

    @app.route("/client_parkings", methods=["GET"])
    def get_client_parking():
        get_clients_is_not_out_parking = (
            db.session.query(ClientParking)
            .filter(ClientParking.time_out == null())
            .all()
        )
        clients_list = [u.to_json() for u in get_clients_is_not_out_parking]
        return jsonify(clients_list), 200

    @app.route("/")
    def start():
        print(datetime.datetime.now())
        return "Автоматизированная парковка"

    return app
