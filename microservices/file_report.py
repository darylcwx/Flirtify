from flask import Flask, jsonify, request, render_template, redirect, url_for, session
from flask_cors import CORS
import os, sys
import psycopg
import requests
from invokes import invoke_http
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import json as jsonnn

conn_string = "postgresql://jeremy:GvtUwDUhQOYrlDC7jEbblg@flirtify-4040.6xw.cockroachlabs.cloud:26257/flirtify.flirtify?sslmode=verify-full"

conn_params = {
    'host':"flirtify-4040.6xw.cockroachlabs.cloud",
    'port':"26257",
    'dbname':"flirtify",
    'user':"jeremy",
    'password':"GvtUwDUhQOYrlDC7jEbblg",
}

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.config['SQLALCHEMY_DATABASE_URI'] = conn_string
app.config['SECRET_KEY'] = 'flirtify_esd_micro'
app.config['SESSION_COOKIE_DOMAIN'] = '127.0.0.1'
app.config['SESSION_COOKIE_PATH'] = '/'
db = SQLAlchemy(app)
CORS(app)

# Configure the SQLAlchemy engine to use CockroachDB
engine = create_engine('cockroachdb+psycopg2://jeremy:GvtUwDUhQOYrlDC7jEbblg@flirtify-4040.6xw.cockroachlabs.cloud:26257/flirtify?sslmode=require')

# Create a SQLAlchemy session factory to manage database connections
Session = sessionmaker(bind=engine)

class Report(db.Model):
    __tablename__ = 'report'
    
    userid = db.Column(db.Integer, primary_key=True)
    otherid = db.Column(db.Integer, primary_key=True)
    matchid = db.Column(db.Integer)
    
    def __init__(self, userid, otherid, matchid):
        self.userid = userid
        self.otherid = otherid
        self.matchid = matchid

def get_conn():
    conn = psycopg.connect(**conn_params, autocommit=True)
    return conn

def run_sql(sql):
    with get_conn() as txn:
        txn.execute(sql)
        
def json(info):
    result = {'info':info[0]}
    result = {"userid":info[0], "otherid":info[1], "matchid":info[2]}
    return result




user_URL = 'http://localhost:26257/user/'
message_URL = 'http://127.0.0.1:5000/api/get_all_messages/'
match_URL = 'http://localhost:5002/match/'

@app.route("/add_report/<string:userid>/<string:otherid>/<string:matchid>")
def add_report(userid, otherid, matchid):
    # print("\nReceived a report from userID:", userid, " reporting userID:", otherid, "\n matchid:", matchid)

    # delete match 
    match_result = invoke_http(match_URL + matchid, method='DELETE', json=None) 
    print('match_result:', match_result)  

    # check messages
    result = checkMsg(otherid, matchid)
    if result == 'api failed to check messages':
        return jsonify(
            {
                "code": 500,
                "data": {
                    "status": 'Check user message failed. Please try again later.'
                    }
            }
        )
    
    elif result == 'no profanities detected':
        return jsonify(
            {
                "code": 200,
                "data": {
                    "status": 'User message did not include any profanities. Report not added.'
                    }
            }
        )

    # add report into database
    get_conn().cursor().execute("INSERT INTO public.report (userid, otherid, matchid) VALUES (%s, %s, %s)", (userid, otherid, matchid))
    reps = get_conn().cursor().execute("SELECT * from public.report WHERE otherid = %s", (otherid,)).fetchall()

    if len(reps) >= 5:
        print('\n\n-----Invoking user microservice-----')
        user_result = invoke_http(user_URL + otherid , method="DELETE", json=None) 
        print('user_result:', user_result)   
        
        report_status = "Number of reports exceeded 5, user deleted"

    else:
        report_status = "Number of reports increased by 1, total reports: " + str(len(reps)+1)

    return jsonify(
            {
                "code": 201,
                "data": {
                    "status": report_status
                    }
            }
        )


# @app.route('/reports')
# def get_reports():
#     reports = get_conn().cursor().execute("SELECT * from public.report").fetchall()
#     if (reports):
#         return jsonify(reports)
#     return jsonify(
#         {
#             "code": 404,
#             "message": "no reports."
#         }
#     ), 404


def checkMsg(otherid, matchid):
    messages = invoke_http(message_URL + matchid, method='GET', json=None) 
    print('msges: ', messages)

    if 'status_message' in messages and messages['status_message'] == 'There are no messages.':
        return 'no profanities detected'

    text = ''
    count = 0
    for msg in messages['messages']:
        print(msg)
        if count > 20:
            break

        elif str(msg['sender_id']) == otherid:
            text += msg['content'] + ' '
            count += 1

    print('text: ', text)
    data = {
        'text': text,
        'mode': 'standard',
        'lang': 'en',
        'opt_countries': 'sg',
        'api_user': '',
        'api_secret': ''
    }

    r = requests.post('https://api.sightengine.com/1.0/text/check.json', data = data)

    output = jsonnn.loads(r.text)
    print(output)

    if output['status'] != 'success':
        return 'api failed to check messages'

    if len(output['profanity']['matches']) == 0:
        return 'no profanities detected'
    
    categories = []
    for item in output['profanity']['matches']:
        categories.append(item['type'])
        return categories


if __name__ == '__main__':
    app.run(port=5015, debug=True)
