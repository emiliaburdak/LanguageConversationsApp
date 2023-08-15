from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

views = Blueprint('views', __name__)


@views.route('/home', methods=['GET'])
@jwt_required()
def home():
    return jsonify({'message': 'Welcome to your dashboard!'})