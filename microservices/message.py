from pyexpat.errors import messages
from flask import Flask, jsonify
from cockroachdb.sqlalchemy import run_transaction
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship


app = Flask(__name__)

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

session = Session()

@app.route('/get_all_messages/<match_id>')
def index(match_id):
    messages = session.query(Message).filter(Message.match_id == match_id).all()

    all_match_messages = []
    for message in messages:
        message_details = {
            'id': message.id,
            'match_id': message.match_id,
            'sender_id': message.sender_id,
            'content': message.content
            }
        all_match_messages.append(message_details)

    # return in json format
    # return jsonify({
    #     'id': message.id,
    #     'match_id': message.match_id,
    #     'sender_id': message.sender_id,
    #     'content': message.content,
    #     })

    return jsonify(all_match_messages)

@app.route('/add_table')
def add_table():
    # Create the database tables
    Base.metadata.create_all(engine)
    return "table created successfully"

@app.route('/add_message')
def add_message():
    #add message to table
    new_message = Message(match_id=1, sender_id=1, content="Hello this is a test entry")
    session.add(new_message)
    session.commit()

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