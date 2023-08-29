from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity
from .models import User, Conversation, Message
from . import db

service = Blueprint("service", __name__)


def get_user_id_by_token_identify():
    username = get_jwt_identity()
    user_object = User.query.filter_by(username=username).first()
    user_id = user_object.id
    return user_id


def find_all_conversations_names_ids():
    user_id = get_user_id_by_token_identify()
    user_conversations = Conversation.query.filter_by(user_id=user_id).all()
    conversations_names_and_ids = [{"id": conversation.id, "name": conversation.conversation_name} for conversation in
                                   user_conversations]
    return conversations_names_and_ids


def find_conversation_by_conversation_id(conversation_id):
    conversation_object = Conversation.query.filter_by(id=conversation_id).first()
    if not conversation_object:
        return jsonify({"error": "Conversation not found"}), 404
    return conversation_object


def save_message_to_database(message_text, conversation_id, is_user):
    new_message = Message(message_text=message_text, conversation_id=conversation_id, is_user=is_user)
    db.session.add(new_message)
    db.session.commit()


def prepare_api_payload(conversation_id):
    conversation_object = find_conversation_by_conversation_id(conversation_id)
    all_conversation_messages = conversation_object.messages
    last_messages = all_conversation_messages[-4:] if len(all_conversation_messages) > 4 else all_conversation_messages
    language = conversation_object.language
    return language, last_messages


def message_for_api(language, last_messages):
    # User response with last 4 messages for context
    messages_for_api = [{"role": "user" if message.is_user else "assistant", "content": message.message_text} for
                        message in last_messages]
    # instruction for chat
    instruction = {"role": "system",
                   "content": f"You are a conversational assistant that speak in {language}. Provide short, concise answers and ask follow-up questions to keep the conversation engaging. adapt the level of difficulty of your speech to your conversation partner"}
    # full info for chat
    messages_for_api.insert(0, instruction)
    return messages_for_api
