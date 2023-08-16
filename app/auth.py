from flask import Blueprint, jsonify, request, make_response
from . import db
from .models import User
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash

auth = Blueprint('auth', __name__)


@auth.route('/signup', methods=['POST'])
def signup():
    signup_data = request.get_json()
    name = signup_data['name']
    username = signup_data['username']
    password = signup_data['password']
    hash_password = generate_password_hash(password)
    new_user = User(name=name, username=username, password=hash_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'Registered successfully!'})


@auth.route('/login', methods=['POST'])
def login():
    form_data = request.get_json()
    form_username = form_data['username']
    form_password = form_data['password']
    user = User.query.filter_by(username=form_username).first()

    if not user or not check_password_hash(user.password, form_password):
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm: "Login required!"'})

    token = create_access_token(identity=user.username)

    return jsonify({'token': token})



