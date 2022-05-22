__version__ = "0.1.0"

from flask import Flask
from flask_restful import Api
from backend.models import db
from backend.resources.users import Users


def create_app():
    app = Flask(__name__)
    app.config.from_object("backend.config")
    api = Api(app)
    db.init_app(app)

    with app.app_context():
        db.create_all()

    # Add resources
    api.add_resource(Users, '/', '/users')

    return app


if __name__ == "__main__":
    create_app().run()