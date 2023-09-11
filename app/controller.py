import json

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
    language = data_from_stt.get("language", None)
    conversation_name = data_from_stt.get("conversation_name", None)
    user_id = get_user_id_by_token_identify()
    if not language or not conversation_name:
        return jsonify({"error": "No conversation name or language"}), 400
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
    stt_message_text = data_from_stt.get("STT_message", None)
    if not stt_message_text:
        return jsonify({"error": "I have technical problem with answer, please repeat"}), 400
    save_message_to_database(stt_message_text, conversation_id, True, None)

    # Api messages preparation
    language, user_message, sum_up_sentence = prepare_api_payload(conversation_id)
    messages_for_api = message_for_api(language, user_message, sum_up_sentence)

    # Api
    openai.api_key = "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"
    response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages_for_api)

    # get chat response
    try:
        chat_message_json = json.loads(response["choices"][0]["message"]["content"])
        chat_message_answer = chat_message_json.get("answer", None)
        chat_message_summary = chat_message_json.get("summary", None)

        # response for user and save to database
        if chat_message_answer:
            response_for_user = chat_message_answer
            save_message_to_database(chat_message_answer, conversation_id, False, chat_message_summary)
        else:
            response_for_user = "I have technical problem with answer, please repeat"

    except (KeyError, json.JSONDecodeError, ValueError):
        response_for_user = "I have technical problem with answer, please repeat"

    return jsonify({"chat_message": response_for_user})


@controller.route("/guidance/<conversation_id>", methods=["POST"])
@jwt_required()
def hint_or_advanced_version(conversation_id):

    # last message (chat_message) and conversation summary
    conversation_object = find_conversation_by_conversation_id(conversation_id)
    if len(conversation_object.messages) > 2:
        last_message = conversation_object.messages[-1].message_text
        summary = conversation_object.messages[-1].summary
    else:
        # frontend: make the advanced_version and hint as not active button
        return jsonify({"error": "Please, start conversation before using hint or sentence advanced correction"}), 400

    # get user message if there is any
    user_attempt = request.get_json(silent=True)

    # create message to chat
    if user_attempt is None:
        guidance_message = {"role": "system",
                            "content": f"this is summary of all conversation '{summary}', give me example answer to this '{last_message}'"}
    else:
        guidance_message = {"role": "system",
                            "content": f"this is summary of all conversation '{summary}', this is last message '{last_message}', transform this '{user_attempt}' to make it more linguistically advanced"}

    # get chat response
    openai.api_key = "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"
    response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=guidance_message)

    # return chat response
    guidance_response = json.loads(response["choices"][0]["message"]["content"])
    return jsonify({"guidance_response": guidance_response})
