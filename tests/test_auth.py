import unittest
from flask_testing import TestCase
import json
from app import db
from app.models import User
from main import app
from werkzeug.security import check_password_hash


class AuthenticationTests(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'  # Use an in-memory database for testing
        return app

    def setUp(self):
        db.create_all()
        self.client.post('signup', json=dict(name='testname', username='testusername', password='testpassword'))

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_successful_signup(self):
        response = self.client.post('signup',
                                    json=dict(name='testname_next', username='testusername_next', password='testpassword_next'))
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['message'], 'Registered successfully!')

    def test_if_user_has_been_correctly_saved_after_signup(self):
        user = User.query.filter_by(username='testusername').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.name, 'testname')
        self.assertEqual(user.username, 'testusername')
        self.assertTrue(check_password_hash(user.password, 'testpassword'))
        self.assertNotEqual(user.password, 'testpassword')

    def test_successful_login(self):
        correct_login = self.client.post('login', json=dict(username='testusername', password='testpassword'))
        self.assertEqual(correct_login.status_code, 200)
        login_data = json.loads(correct_login.data.decode('utf-8'))
        self.assertIsNotNone(login_data['token'])

    def test_login_with_incorrect_username(self):
        incorrect_username_login = self.client.post('login',
                                                    json=dict(username='failusername', password='testpassword'))
        self.assertEqual(incorrect_username_login.status_code, 401)

    def test_login_with_incorrect_password(self):
        incorrect_password_login = self.client.post('login',
                                                    json=dict(username='testusername', password='failpassword'))
        self.assertEqual(incorrect_password_login.status_code, 401)


if __name__ == '__main__':
    unittest.main()
