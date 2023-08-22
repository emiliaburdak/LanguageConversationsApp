from flask import Blueprint, jsonify, request, make_response
from flask_jwt_extended import jwt_required
from flask_jwt_extended import get_jwt_identity
from .models import User, Conversation, Message
from . import db
import openai

controller = Blueprint('controller', __name__)


def get_user_id_by_token_identify():
    username = get_jwt_identity()
    user_object = User.query.filter_by(username=username).first()
    user_id = user_object.id
    return user_id


def find_all_conversations_names():
    all_existing_conv_names_tuples = Conversation.query.with_entities(Conversation.conversation_name).all()
    all_existing_conv_names = [conversation_name[0] for conversation_name in all_existing_conv_names_tuples]
    return all_existing_conv_names


def find_all_conversation_id():
    all_existing_conv_id_tuples = Conversation.query.with_entities(Conversation.id).all()
    all_existing_conv_id = [conversation_id[0] for conversation_id in all_existing_conv_id_tuples]
    return all_existing_conv_id


def find_conversation_by_conversation_id(conversation_id):
    conversation_object = Conversation.query.filter_by(id=conversation_id).first()
    if not conversation_object:
        return jsonify({'error': 'Conversation not found'}), 404
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


@controller.route('/home', methods=['GET'])
@jwt_required()
def home():
    username = get_jwt_identity()  # fetch actual useraname of user that is invoking this method
    return jsonify({'message': 'Welcome to home!', 'username': username})


@controller.route('/create_new_conversation', methods=['POST'])
@jwt_required()
def create_new_conversation():
    data_from_stt = request.get_json()
    # assume that this json looks like this: {language='spanish', conversation_name= 'conv123'}
    language = data_from_stt['language']
    conversation_name = data_from_stt['conversation_name']
    user_id = get_user_id_by_token_identify()
    new_conversation = Conversation(conversation_name=conversation_name, user_id=user_id, language=language)

    db.session.add(new_conversation)
    db.session.commit()

    return jsonify({'name': new_conversation.conversation_name, 'id': new_conversation.id})


@controller.route('/existing_conversations', methods=['GET'])
@jwt_required()
def existing_conversations():
    all_existing_conv_names = find_all_conversations_names()
    all_existing_conv_id = find_all_conversation_id()
    return jsonify({'names': all_existing_conv_names, 'ids': all_existing_conv_id})


@controller.route('/continue_this_conversations/<conversation_id>', methods=['GET'])
@jwt_required()
def continue_this_conversations(conversation_id):
    conversation_object = find_conversation_by_conversation_id(conversation_id)
    all_conversation_messages = conversation_object.messages
    messages_lies_text_id_time = [[message.message_text, message.id, message.timestamp] for message in
                                  all_conversation_messages]
    return jsonify({'message_info': messages_lies_text_id_time})


@controller.route('/speak/<conversation_id>', methods=['POST'])
@jwt_required()
def get_chat_response(conversation_id):
    # save to database stt
    # assume that this json looks like this: {TTS_message='blabla'}
    data_from_stt = request.get_json()
    stt_message_text = data_from_stt['TTS_message']
    save_message_to_database(stt_message_text, conversation_id, True)

    # Api messages preparation
    language, last_messages = prepare_api_payload(conversation_id)
    messages_for_api = message_for_api(language, last_messages)

    # Api
    openai.api_key = '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'
    response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages_for_api)

    # save chat answer to database
    chat_message_text = response['choices'][0]['message']['content']
    save_message_to_database(chat_message_text, conversation_id, False)

    return jsonify({'chat_message': chat_message_text})
