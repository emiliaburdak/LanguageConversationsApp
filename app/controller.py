from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from flask_jwt_extended import get_jwt_identity
from .models import User, Conversation, Message
from . import db
import openai
from .service import (get_user_id_by_token_identify, find_all_conversations_names_ids,
                      find_conversation_by_conversation_id, save_message_to_database,
                      prepare_api_payload, message_for_api)

controller = Blueprint("controller", __name__)


@controller.route("/home", methods=["GET"])
@jwt_required()
def home():
    username = get_jwt_identity()  # fetch actual useraname of user that is invoking this method
    return jsonify({"message": "Welcome to home!", "username": username})


@controller.route("/conversation", methods=["POST"])
@jwt_required()
def create_conversation():
    data_from_stt = request.get_json()
    # assume that this json looks like this: {language='spanish', conversation_name= 'conv123'}
    language = data_from_stt["language"]
    conversation_name = data_from_stt["conversation_name"]
    user_id = get_user_id_by_token_identify()
    new_conversation = Conversation(conversation_name=conversation_name, user_id=user_id, language=language)

    db.session.add(new_conversation)
    db.session.commit()

    return jsonify({"name": new_conversation.conversation_name, "id": new_conversation.id})


@controller.route("/conversations", methods=["GET"])
@jwt_required()
def get_conversations():
    # [{name: convoname, id: 1}, {name: blah, id: 2}]
    all_conversations_names_ids = find_all_conversations_names_ids()
    if all_conversations_names_ids is None:
        return jsonify([])
    return jsonify(all_conversations_names_ids)


@controller.route("/conversation/<conversation_id>", methods=["GET"])
@jwt_required()
def get_conversation(conversation_id):
    conversation_object = find_conversation_by_conversation_id(conversation_id)

    name = conversation_object.conversation_name
    beginning_date = conversation_object.beginning_date
    last_messaged_date = conversation_object.last_messaged_date
    language = conversation_object.language

    conversation_messages = conversation_object.messages
    messages_data = [{"id": message.id, "is_user": message.is_user, "message_text": message.message_text,
                      "timestamp": message.timestamp} for message in conversation_messages]

    return jsonify({"id": conversation_id, "conversation_name": name, "beginning_date": beginning_date,
                    "last_message_date": last_messaged_date, "language": language, "messages": messages_data})


@controller.route("/response/<conversation_id>", methods=["POST"])
@jwt_required()
def get_chat_response(conversation_id):
    # save to database stt
    # assume that this json looks like this: {TTS_message='blabla'}
    data_from_stt = request.get_json()
    stt_message_text = data_from_stt["TTS_message"]
    save_message_to_database(stt_message_text, conversation_id, True)

    # Api messages preparation
    language, last_messages = prepare_api_payload(conversation_id)
    messages_for_api = message_for_api(language, last_messages)

    # Api
    openai.api_key = "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"
    response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages_for_api)

    # save chat answer to database
    chat_message_text = response["choices"][0]["message"]["content"]
    save_message_to_database(chat_message_text, conversation_id, False)

    return jsonify({"chat_message": chat_message_text})
