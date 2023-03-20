from pyexpat.errors import messages
from flask import Flask, jsonify, request, render_template, redirect, url_for, session
from cockroachdb.sqlalchemy import run_transaction
from numpy import mat
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship


app = Flask(__name__, template_folder='../templates')
app.secret_key = 'flirtify_esd_micro'

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

@app.route('/get_all_messages/<match_id>')
def index(match_id):
    session['user_id'] = 1
    logged_in_user = session['user_id']

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
        return render_template('message.html', success="Message was successfully sent!", all_messages=all_match_messages, user_id=logged_in_user, match_id=match_id)
    else:
        return render_template('message.html', all_messages=all_match_messages, user_id=logged_in_user, match_id=match_id)

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
                    "code": 404,
                    "status_message": "There are no messages."
                }
            ), 404

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
    except Exception as e:
        session_db.rollback()
        app.logger.error(f"Error committing session: {str(e)}")
        return "There was an error sending your message. Please try again."

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
    app.run(debug=True)
