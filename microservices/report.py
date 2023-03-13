from flask import Flask, request, jsonify
from flask_cors import CORS

import os, sys

import requests
from invokes import invoke_http

app = Flask(__name__)
CORS(app)

user_url = 'http://localhost:5000/person'
message_url = 'http://localhost:5001/message'
match_url = 'http://localhost:5002/match'

if __name__ == '__main__':
    app.run(port=5005, debug=True)
