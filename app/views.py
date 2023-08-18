from flask import Blueprint, jsonify, request, make_response
from flask_jwt_extended import jwt_required
from flask_jwt_extended import get_jwt_identity
from models import User, Conversation, Message
from . import db
import openai
import os

views = Blueprint('views', __name__)


def get_user_id_by_token_identify():
    username = get_jwt_identity()
    user_object = User.query.filter_by(username=username).first()
    user_id = user_object.id
    return user_id


@views.route('/home', methods=['GET'])
@jwt_required()
def home():
    username = get_jwt_identity() # fetch actual useraname of user that is invoking this method
    return jsonify({'message': 'Welcome to home!', 'username': username})


@views.route('/create_new_conversation', methods=['GET'])
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

    return jsonify({'new_conversation': new_conversation})


@views.route('/speak/<conversation_id>', methods=['GET'])
@jwt_required()
def speak(conversation_id):

    # save to database stt

    # jak rozróżnia te jsnoy ? skąd wie że get_json to ten co ma te dane ? gdzieś na frontendzie się przekazuje jaka to funkcja i stąd czy jak ?
    data_from_stt = request.get_json()
    # assume that this json looks like this: {stt_message='blabla', language='spanish', conversation_name= 'dupal123'}
    stt_message_text = data_from_stt['TTS_message']
    new_message_stt = Message(message_text=stt_message_text, conversation_id=conversation_id, is_user=True)

    db.session.add(new_message_stt)
    db.session.commit()

    # APIAPIAPIAPIAPIAPIAPIAPIAPI

    conversation_object = Conversation.query.filter_by(conversation_id=conversation_id).first()
    if not conversation_object:
        return jsonify({'error': 'Conversation not found'}), 404

    all_conversation_messages = conversation_object.messages
    last_messages = all_conversation_messages[-4:] if len(all_conversation_messages) > 4 else all_conversation_messages

    # User response with last 4 messages for context
    messages_for_api = [{"role": "user" if message.is_user else "assistant", "content": message.message_text} for
                        message in last_messages]

    # instruction for chat
    instruction = {"role": "system", "content": "You are a conversational assistant. Provide short, concise answers and ask follow-up questions to keep the conversation engaging."}

    # full info for chat
    messages_for_api.insert(0, instruction)

    # Api
    openai.api_key = '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'

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages_for_api
    )

    print(response.choices[0].message)

    # save chat answer to database

    chat_message_text = response['choices'][0]['message']['content']
    new_message_chat = Message(message_text=chat_message_text, conversation_id=conversation_id, is_user=False)

    db.session.add(new_message_chat)
    db.session.commit()

    return jsonify({'chat_message': chat_message_text})



