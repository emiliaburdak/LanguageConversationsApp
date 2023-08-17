from . import db
import datetime


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    conversations = db.relationship('Conversation', backref='user', passive_deletes=True)


class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_name = db.Column(db.String(80), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    beginning_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    last_messaged_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    messages = db.relationship('Message', backref='conversation', passive_deletes=True)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id', ondelete='CASCADE'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    message_text = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)


