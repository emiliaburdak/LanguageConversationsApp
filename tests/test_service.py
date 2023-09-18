import json
import unittest
from unittest.mock import patch

from flask_testing import TestCase
from werkzeug.security import generate_password_hash
from flask_jwt_extended import verify_jwt_in_request
from app.service import find_all_conversations_names_ids, get_user_id_by_token_identify, \
    find_conversation_by_conversation_id, save_message_to_database, prepare_api_payload, message_for_api, \
    prepare_messages, call_chat_response
from app import db
from app.models import User, Conversation, Message
from main import app
from app.controller import ChatAPIError



class ServiceTests(TestCase):

    def create_app(self):
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"  # Use an in-memory database for testing
        return app

    def setUp(self):
        db.session.remove()
        db.drop_all()
        db.create_all()
        hashed_password = generate_password_hash("testpassword", method="sha256")
        self.test_user = User(
            username="testuser",
            name="Test User",
            password=hashed_password
        )
        db.session.add(self.test_user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_login_required(self):
        login = self.client.post("login", json=dict(username="testuser", password="testpassword"))
        login_data = json.loads(login.data.decode("utf-8"))
        bearer_token = login_data["token"]
        return bearer_token

    def test_get_user_id_by_token_identify(self):
        bearer_token = self.test_login_required()

        # "Hey Flask, I want to simulate an HTTP request for this app."
        with self.app.test_request_context(headers={"Authorization": f"Bearer {bearer_token}"}):
            # if you want to manually ensure a JWT's presence
            verify_jwt_in_request()

            user_id = get_user_id_by_token_identify()
            self.assertEqual(user_id, 1)

    def add_conversation_and_message(self):
        conversation1 = Conversation(conversation_name="Test Conversation 1", user_id=self.test_user.id,
                                     language="Spanish")
        db.session.add(conversation1)
        db.session.commit()
        message1 = Message(message_text="Hello", conversation_id=conversation1.id, is_user=True, summary="Test")
        message2 = Message(message_text="Hello Again", conversation_id=conversation1.id, is_user=True, summary=None)
        db.session.add(message1)
        db.session.add(message2)
        db.session.commit()

    def test_find_all_conversations_names_ids(self):
        self.add_conversation_and_message()
        bearer_token = self.test_login_required()
        with self.app.test_request_context(headers={"Authorization": f"Bearer {bearer_token}"}):
            verify_jwt_in_request()
            conversations_names_and_ids = find_all_conversations_names_ids()
            self.assertEqual(conversations_names_and_ids[0]["id"], 1)
            self.assertEqual(conversations_names_and_ids[0]["name"], "Test Conversation 1")

    def test_find_conversation_by_conversation_id(self):
        self.add_conversation_and_message()
        correct_conversation_object = find_conversation_by_conversation_id(1)
        json_error, status_code = find_conversation_by_conversation_id(5)
        self.assertEqual(correct_conversation_object.id, 1)
        self.assertEqual(correct_conversation_object.conversation_name, "Test Conversation 1")
        self.assertEqual(correct_conversation_object.language, "Spanish")
        self.assertEqual(json_error.json, {"error": "Conversation not found"})
        self.assertEqual(status_code, 404)

    def test_save_message_to_database(self):
        self.add_conversation_and_message()
        save_message_to_database("test_mess", 1, True, None)
        conversation_object = find_conversation_by_conversation_id(1)
        self.assertEqual(conversation_object.id, 1)
        self.assertEqual(conversation_object.messages[0].message_text, "Hello")
        self.assertEqual(conversation_object.messages[2].message_text, "test_mess")
        self.assertEqual(conversation_object.messages[2].summary, None)

    def test_prepare_api_payload_empty_summary(self):
        self.test_save_message_to_database()
        conversation_object = find_conversation_by_conversation_id(1)
        language, user_message, sum_up_sentence = prepare_api_payload(conversation_object.id)
        self.assertEqual(sum_up_sentence, None)
        self.assertEqual(language, conversation_object.language)
        self.assertEqual(user_message, "test_mess")

    def test_prepare_api_payload(self):
        self.add_conversation_and_message()
        conversation_object = find_conversation_by_conversation_id(1)
        language, user_message, sum_up_sentence = prepare_api_payload(conversation_object.id)
        self.assertEqual(sum_up_sentence, "Test")
        self.assertEqual(language, conversation_object.language)
        self.assertEqual(user_message, "Hello Again")

    def test_message_for_api(self):
        formatted_messages = message_for_api("Spanish", "Test", "Testing")
        self.assertEqual(formatted_messages, [{"role": "system",
                                               "content": f"You must return your whole response in JSON. You're a chat assistant fluent in Spanish. Always begin with a summary sentence (max 15 words). Then, provide a concise answer or question (max 10 words) related to Testing. \n \n It's crucial to respond ONLY in format with key such as summary and answer. Only JSON allowed"},
                                              {"role": "user", "content": "Test"}])

    def test_message_for_api_empty_summary(self):
        formatted_messages = message_for_api("Spanish", "Test", None)
        self.assertEqual(formatted_messages, [{"role": "system",
                                               "content": f"You must return your whole response in JSON. You're a chat assistant fluent in Spanish. Always begin with a summary sentence (max 15 words). Then, provide a concise answer or question (max 10 words) related to sentence. \n \n It's crucial to respond ONLY in format with key such as summary and answer. Only JSON allowed"},
                                              {"role": "user", "content": "Test"}])

    def test_prepare_messages(self):
        self.add_conversation_and_message()
        last_message, summary = prepare_messages(1)
        self.assertEqual(last_message, "Hello Again")
        self.assertEqual(summary, None)

    def test_prepare_messages_no_messages(self):
        conversation1 = Conversation(conversation_name="Test Conversation 1", user_id=self.test_user.id,
                                     language="Spanish")
        db.session.add(conversation1)
        db.session.commit()
        self.assertRaises(ValueError, lambda: prepare_messages(1))

    def test_call_chat_response_hint_message(self):
        summary = "testing"
        last_message = "testing this function"
        hint_message = [{"role": "user",
                             "content": f"{summary}, give me only one sentence example answer to this '{last_message}'"}]
        mock_response = {
            "choices": [
                {
                    "message": {
                        "content": f"mock response"
                    }
                }
            ]
        }
        with patch("openai.ChatCompletion.create", return_value=mock_response):
            hint_response = call_chat_response(hint_message)
            self.assertEqual(hint_response, "mock response")


    def test_call_chat_response_advance_version(self):
        summary = "testing"
        last_message = "testing this function"
        user_attempt_message = "test if you can make this sentence better"
        advance_version_message = [{"role": "user",
                             "content": f"{summary}, this is last message '{last_message}', transform this '{user_attempt_message}' to make it more linguistically advanced"}]
        mock_response = {
            "choices": [
                {
                    "message": {
                        "content": f"mock response"
                    }
                }
            ]
        }
        with patch("openai.ChatCompletion.create", return_value=mock_response):
            advance_version_response = call_chat_response(advance_version_message)
            self.assertEqual(advance_version_response, "mock response")

    def test_call_chat_response_error(self):
        summary = "testing"
        last_message = "testing this function"
        guidance_message = [{"role": "user",
                             "content": f"{summary}, give me only one sentence example answer to this '{last_message}'"}]
        with patch("openai.ChatCompletion.create", side_effect=ChatAPIError("Failed to get a response from the chat")):
            self.assertRaises(ChatAPIError, lambda: call_chat_response(guidance_message))


if __name__ == "__main__":
    unittest.main()
