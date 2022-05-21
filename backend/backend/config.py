# Statement for enabling the development environment
DEBUG = True

# Define the application directory
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_DIR = os.path.join(BASE_DIR, "database")
if not os.path.isdir(DATABASE_DIR):
    os.mkdir(DATABASE_DIR)

SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(DATABASE_DIR, "app.db")
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Secret key for signing cookies
SECRET_KEY = "secret"
