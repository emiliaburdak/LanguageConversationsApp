import unittest
from flask_testing import TestCase
import json
from app import db
from app.models import User, Conversation, Message
from main import app


class ControllerTests(TestCase):

    def create_app(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'  # Use an in-memory database for testing
        return app

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

