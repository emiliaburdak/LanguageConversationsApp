from flask import Flask
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from os import path


db = SQLAlchemy()
jwt = JWTManager()
DB_NAME = "database.db"


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'YOUR_SECRET_KEY'
    app.config['JWT_SECRET_KEY'] = 'YOUR_JWT_SECRET_KEY'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    # from .models import User, Post, Comments, Likes

    with app.app_context():
        db.create_all()

    return app


def create_detabase(app):
    if not path.exists('app/' + DB_NAME):
        db.create_all()