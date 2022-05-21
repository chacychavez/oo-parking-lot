from backend.models import db, Base

# Define a User model
class User(Base):

    __tablename__ = "user"

    # User Name
    name = db.Column(db.String(128), nullable=False)

    # New instance instantiation procedure
    def __init__(self, name):

        self.name = name

    def __repr__(self):
        return "<User %r>" % (self.name)
