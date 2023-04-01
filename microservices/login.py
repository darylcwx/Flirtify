from flask import Flask, jsonify, request, render_template, redirect, url_for, session
from flask_cors import CORS
from cockroachdb.sqlalchemy import run_transaction
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
import requests
import json

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

session_db = Session()

# Logging in
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    print(data)
    email = data['email']
    password = data['password']
    url = f"http://localhost:26257/user/{email}/{password}"
    user = requests.get(url).json()
    try:
        if user['data'] == None:
            return jsonify({'data': None, 'message': 'User does not exist'})
        else:
            session['user_id'] = user['data']['id']
            return jsonify({'data': user['data'], 'message': 'Login Successful'})
    except json.decoder.JSONDecodeError:
        print('The string is not in JSON format')
        print('=======================')
        print(email)
        print(password)
        print('=======================')
        print(user)
        print('=======================')

    
# Successful login
@app.route('/login_success')
def login_success():
    user_id = session['user_id']
    if not user_id:
        return redirect(url_for('login'))
    return render_template('home.html', user_id=user_id)
    

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    # return render_template('login.html')
    return jsonify({'data': None, 'message': 'Logout Successful'})

if __name__ == '__main__':
    app.run(port=5009, debug=True)