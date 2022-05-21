import uuid
import datetime

from backend.models import db
from backend.models.users import User

def get_all_users():
    return User.query.all()

def save_changes(data):
    db.session.add(data)
    db.session.commit()