import factory
import factory.fuzzy as fuzzy
from factory.faker import faker

import random

from ..main.app import db
from ..main.models import Parking, Client


class ClientFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Client
        sqlalchemy_session = db.session

    name = factory.Faker('first_name')
    surname = factory.Faker('last_name')
    credit_card = factory.Faker('boolean')
    car_number = factory.Faker('license_plate')


fake = faker.Faker()


class ParkingFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Parking
        sqlalchemy_session = db.session

    address = fake.address()
    opened = factory.Faker('boolean')
    count_places = fuzzy.FuzzyInteger(50, 150)
    count_available_places = factory.LazyAttribute(lambda x: random.randrange(50, 150))
