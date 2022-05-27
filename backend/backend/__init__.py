__version__ = "0.1.0"

from flask import Flask

from backend.controllers import parking


def create_app():
    app = Flask(__name__)
    app.config.from_object("backend.config")

    # Register blueprints
    app.register_blueprint(parking, url_prefix="/parking")

    return app


if __name__ == "__main__":
    create_app().run()
