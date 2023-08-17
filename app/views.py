from flask import Blueprint, jsonify, request, make_response
from flask_jwt_extended import jwt_required
from flask_jwt_extended import get_jwt_identity
from models import User, Conversation, Message
from . import db

views = Blueprint('views', __name__)

chat = User(id=0, username="firendly_chat", name='Friend', password='XXX')
db.session.add(chat)
db.session.commit()

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
    return jsonify({'new_conversation': new_conversation})


@views.route('/speak/<conversation_id>', methods=['GET'])
@jwt_required()
def speak(conversation_id):

    # save to database stt

    # jak rozróźnia te jsnoy ? skąd wie że get_json to ten co ma te dane ? gdzieś na frontendzie się przekazuje jaka to funkcja i stąd czy jak ?
    data_from_stt = request.get_json()
    # assume that this json looks like this: {stt_message='blabla', language='spanish', conversation_name= 'dupal123'}
    stt_message_text = data_from_stt['TTS_message']
    author_id = get_user_id_by_token_identify()
    Message(message_text=stt_message_text, author_id=author_id, conversation_id=conversation_id)

    # APIAPIAPIAPIAPIAPIAPIAPIAPI
    # api_response looks like : {
    #   "choices": [
    #     {
    #       "finish_reason": "stop",
    #       "index": 0,
    #       "message": {
    #         "content": "The 2020 World Series was played in Texas at Globe Life Field in Arlington.",
    #         "role": "assistant"
    #       }
    #     }
    #   ],
    #   "created": 1677664795,
    #   "id": "chatcmpl-7QyqpwdfhqwajicIEznoc6Q47XAyW",
    #   "model": "gpt-3.5-turbo-0613",
    #   "object": "chat.completion",
    #   "usage": {
    #     "completion_tokens": 17,
    #     "prompt_tokens": 57,
    #     "total_tokens": 74
    #   }
    # }


    # save chat answer to database

    response = {}
    chat_message_text = response['choices'][0]['message']['content']
    author_id = 0
    Message(message_text=chat_message_text, author_id=author_id, conversation_id=conversation_id)

    return jsonify({'chat_message': chat_message_text})



