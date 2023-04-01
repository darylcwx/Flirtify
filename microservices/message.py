from pyexpat.errors import messages
from flask import Flask, jsonify, request, render_template, redirect, url_for, session
from flask_cors import CORS
from cockroachdb.sqlalchemy import run_transaction
from numpy import mat
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
import requests


app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.config['SECRET_KEY'] = 'flirtify_esd_micro'
app.config['SESSION_COOKIE_DOMAIN'] = '127.0.0.1'
app.config['SESSION_COOKIE_PATH'] = '/'
CORS(app)

# Configure the SQLAlchemy engine to use CockroachDB
engine = create_engine('cockroachdb://jeremy:GvtUwDUhQOYrlDC7jEbblg@flirtify-4040.6xw.cockroachlabs.cloud:26257/flirtify?sslmode=require')

# Create a SQLAlchemy session factory to manage database connections
Session = sessionmaker(bind=engine)

# Create a base class for database models
Base = declarative_base()

class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(Integer, nullable=False)
    sender_id = Column(Integer, nullable=False)
    content = Column(String, nullable=False)

    def __init__(self, match_id, sender_id, content):
        self.match_id = match_id
        self.sender_id = sender_id
        self.content = content

    def json(self):
        result = {
            'id'        : self.id,
            'match_id'  : self.match_id,
            'sender_id' : self.sender_id,
            'content'   : self.content
        }
        return result

session_db = Session()

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/matches')
def matches():
    return render_template('matches.html')

@app.route('/get_all_messages/<match_id>')
def index(match_id):
    # session storing of user id but this will be replaced by the session storage when user logs in
    session['user_id'] = 849811382203678721
    logged_in_user = session['user_id']

    url = f"http://localhost:5002/match/{match_id}"
    match = requests.get(url).json()
    
    user_id1 = match['data']['user_id1']
    user_id2 = match['data']['user_id2']

    if logged_in_user == user_id1:
        receiving_user = user_id2
    else:
        receiving_user = user_id1

    url = f"http://localhost:26257/user/{str(receiving_user)}"
    receiving_user_object = requests.get(url).json()

    receiving_user_name = receiving_user_object['data']['firstname']

    messages = session_db.query(Message).filter(Message.match_id == match_id).all()

    all_match_messages = []
    if len(messages):
        for message in messages:
            message_details = {
                'id': message.id,
                'match_id': message.match_id,
                'sender_id': message.sender_id,
                'content': message.content
                }
            all_match_messages.append(message_details)

    redirect_from = request.args.get('redirect_from')
    if redirect_from:
        return render_template('message.html', success="Message was successfully sent!", all_messages=all_match_messages, user_id=logged_in_user, receiving_user_name=receiving_user_name, match_id=match_id)
    else:
        return render_template('message.html', all_messages=all_match_messages, user_id=logged_in_user, receiving_user_name=receiving_user_name, match_id=match_id)

    # return in json format
    # return jsonify({
    #     'id': message.id,
    #     'match_id': message.match_id,
    #     'sender_id': message.sender_id,
    #     'content': message.content,
    #     })

    # return all_match_messages

@app.context_processor
def inject_navbar():
    return dict(navbar="navbar.html")

@app.route('/api/get_all_messages/<match_id>')
def get_messages(match_id):
    messages = session_db.query(Message).filter(Message.match_id == match_id).all()

    if len(messages):
        all_match_messages = []
        for message in messages:
                message_details = {
                    'id': message.id,
                    'match_id': message.match_id,
                    'sender_id': message.sender_id,
                    'content': message.content
                    }
                all_match_messages.append(message_details)

        return jsonify(
                {
                    "code": 200,
                    "messages": all_match_messages
                }
            )
    else:
        return jsonify(
                {
                    "code": 400,
                    "status_message": "There are no messages."
                }
            ), 400

@app.route('/send_message/<user_id>/<match_id>', methods=['POST'])
def send_message(user_id, match_id):
    new_message = Message(
        match_id = match_id,
        sender_id = user_id,
        content = request.form['content']
        )

    try:
        session_db.add(new_message)
        session_db.commit()

        return jsonify(
            {
                "code": 201,
                "message": "Message successfully sent"
            }
        ), 201
        
    except Exception as e:
        session_db.rollback()
        app.logger.error(f"Error committing session: {str(e)}")
        return jsonify(
            {
                "code": 500,
                "message": "There was an error sending your message. Please try again."
            }
        ), 500

        # return "There was an error sending your message. Please try again."

    success_message = "Message was successfully sent!"

    # return render_template('message.html', success=success_message)
    return redirect(url_for('index', match_id=match_id, redirect_from='send_message'))

@app.route('/add_table')
def add_table():
    # Create the database tables
    Base.metadata.create_all(engine)
    return "table created successfully"

@app.route('/add_message')
def add_message():
    #add message to table
    new_message = Message(match_id=1, sender_id=1, content="Hello wassup")
    session_db.add(new_message)
    session_db.commit()

    return "message added successfully"

@app.route('/drop_table')
def drop_table():
    # Drop the table
    def drop_table(txn):
        txn.execute("DROP TABLE messages")
    run_transaction(engine, drop_table)

    return 'Table dropped successfully.'

if __name__ == '__main__':
    app.run(port=5000, debug=True)
