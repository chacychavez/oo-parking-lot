
from flask_restful import Resource, Api
from backend.controllers.users import get_all_users

class Users(Resource):
    def get(self):
        return "Get Users"