import json
import deepl

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from flask_jwt_extended import get_jwt_identity

from .models import User, Conversation, Message, Dictionary
from . import db
import openai
from .service import (get_user_id_by_token_identify, find_all_conversations_names_ids,
                      find_conversation_by_conversation_id, save_message_to_database,
                      prepare_api_payload, message_for_api, call_chat_response, prepare_messages, ChatAPIError)

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
    stt_message_text = data_from_stt.get("TTS_message", None)
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


@controller.route("/hint/<conversation_id>", methods=["POST"])
@jwt_required()
def get_hint(conversation_id):
    try:
        last_message, summary = prepare_messages(conversation_id)
        guidance_message = [{"role": "user",
                             "content": f"{summary}, give me only one sentence example answer to this '{last_message}'"}]
        # get chat_response
        guidance_response = call_chat_response(guidance_message)
        return jsonify({"guidance_response": guidance_response}), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except ChatAPIError as e:
        return jsonify({"error": str(e)}), 500


@controller.route("/advanced_version/<conversation_id>", methods=["POST"])
@jwt_required()
def get_advanced_version(conversation_id):
    try:
        last_message, summary = prepare_messages(conversation_id)

        # handle invalid input
        user_attempt = request.get_json(silent=True)
        if user_attempt is None:
            return jsonify({"error": "There is no sentence to correct, please use hint instead"})

        # create message to chat
        user_attempt_message = user_attempt["chat_message"]
        guidance_message = [{"role": "user",
                             "content": f"{summary}, this is last message '{last_message}', transform this '{user_attempt_message}' to make it more linguistically advanced"}]
        # get chat_response
        guidance_response = call_chat_response(guidance_message)
        return jsonify({"guidance_response": guidance_response}), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except ChatAPIError as e:
        return jsonify({"error": str(e)}), 500


@controller.route("/translation", methods=["POST"])
@jwt_required()
def get_translation():
    to_translate_data = request.get_json()
    word_to_translate = to_translate_data["word_to_translate"]
    sentence_to_translate = to_translate_data["sentence_to_translate"]
    source_lang = to_translate_data["source_lang"]
    target_lang = to_translate_data["target_lang"]

    auth_key = "909e67c2-5f8d-8fe9-8432-a790ba0061b2:fx"
    translator = deepl.Translator(auth_key)

    word_translation = translator.translate_text(word_to_translate, source_lang=source_lang, target_lang=target_lang)
    sentence_translation = translator.translate_text(sentence_to_translate, source_lang=source_lang,
                                                     target_lang=target_lang)
    return jsonify({"word_translation": word_translation.text, "sentence_translation": sentence_translation.text}), 200


def save_to_db_dictionary(word_to_dictionary, translated_word, contex_sentence, source_lang, target_lang,
                          translated_contex_sentence):
    user_id = get_user_id_by_token_identify()
    new_word = Dictionary(user_id=user_id, word_to_dictionary=word_to_dictionary, translated_word=translated_word,
                          contex_sentence=contex_sentence, source_lang=source_lang, target_lang=target_lang,
                          translated_contex_sentence=translated_contex_sentence)
    db.session.add(new_word)
    db.session.commit()


@controller.route("/dictionary", methods=["POST"])
@jwt_required()
def add_to_dictionary():
    to_dictionary_data = request.get_json()
    word_to_dictionary = to_dictionary_data["word_to_dictionary"]
    contex_sentence = to_dictionary_data["contex_sentence"]
    source_lang = to_dictionary_data["source_lang"]
    target_lang = to_dictionary_data["target_lang"]

    # translate-deepl
    auth_key = "909e67c2-5f8d-8fe9-8432-a790ba0061b2:fx"
    translator = deepl.Translator(auth_key)

    word_translation = translator.translate_text(word_to_dictionary, source_lang=source_lang, target_lang=target_lang)
    sentence_translation = translator.translate_text(contex_sentence, source_lang=source_lang,
                                                     target_lang=target_lang)
    translated_word = word_translation.text
    translated_contex_sentence = sentence_translation.text

    # save to db
    save_to_db_dictionary(word_to_dictionary, translated_word, contex_sentence, source_lang, target_lang,
                          translated_contex_sentence)

    return jsonify({"translated_word": translated_word, "translated_contex_sentence": translated_contex_sentence}), 200
