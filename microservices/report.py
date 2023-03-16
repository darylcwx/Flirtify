from flask import Flask, request, jsonify
from flask_cors import CORS
import os, sys
import psycopg
import requests
from invokes import invoke_http
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

conn_string = "postgresql://jeremy:GvtUwDUhQOYrlDC7jEbblg@flirtify-4040.6xw.cockroachlabs.cloud:26257/flirtify.flirtify?sslmode=verify-full"

conn_params = {
    'host':"flirtify-4040.6xw.cockroachlabs.cloud",
    'port':"26257",
    'dbname':"flirtify",
    'user':"jeremy",
    'password':"GvtUwDUhQOYrlDC7jEbblg",
}

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = conn_string
db = SQLAlchemy(app)
CORS(app)

# Configure the SQLAlchemy engine to use CockroachDB
engine = create_engine('cockroachdb://jeremy:GvtUwDUhQOYrlDC7jEbblg@flirtify-4040.6xw.cockroachlabs.cloud:26257/flirtify?sslmode=require')

# Create a SQLAlchemy session factory to manage database connections
Session = sessionmaker(bind=engine)

class Report(db.Model):
    __tablename__ = 'report'
    
    userid = db.Column(db.Integer, primary_key=True)
    otherid = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(256), nullable=False)
    message = db.Column(db.String(256), nullable=False)
    
    def __init__(self, userid, otherid, category, message):
        self.userid = userid
        self.otherid = otherid
        self.category = category
        self.message = message

def get_conn():
    conn = psycopg.connect(**conn_params, autocommit=True)
    return conn

def run_sql(sql):
    with get_conn() as txn:
        txn.execute(sql)
        
def json(info):
    result = {'info':info[0]}
    result = {"userid":info[0], "otherid":info[1], "category":info[2], "message":info[3]}
    return result

user_URL = 'http://localhost:5000/person'
message_URL = 'http://localhost:5001/message'
match_URL = 'http://localhost:5002/match/'

@app.route("/add_report/<string:ids>/<string:category>/<string:message>")
def add_report(ids, category, message):
    userid, otherid, matchid = ids.split(',')
    print("\nReceived a report from userID:", userid, " reporting userID:", otherid, "\n category:", category, ", regarding: ", message)

    # 1. delete match 
    # print('\n-----Invoking match microservice-----')

    # match_result = invoke_http(match_URL + matchid, method='DELETE', json=None) 
    # print('match_result:', match_result)  

    # reps = cur.execute("SELECT * from public.report WHERE otherid = %s", (otherid,))
    reps = get_conn().cursor().execute("SELECT * from public.report WHERE otherid = %s", (otherid,)).fetchall()
    if len(reps) >= 5:
        # exceeded
        print('\n\n-----Invoking user microservice-----')
        user_result = invoke_http(user_URL + otherid , method="DELETE", json=None) 
        print('user_result:', user_result)   
        report_status = "Number of reports exceeded 5, user deleted"

    elif checkMsg(message):
        # havent exceed, increment by 1
        get_conn().cursor().execute("INSERT INTO public.report (userid, otherid, category, message) VALUES (%s, %s, %s, %s)", (userid, otherid, category, message,))
        report_status = "Number of reports increased by 1"


    report = get_conn().cursor().execute("SELECT * from public.report WHERE userid = %s AND otherid = %s", (userid, otherid, )).fetchone()
    return jsonify(
            {
                "code": 201,
                "data": {
                    "report": json(report),
                    "status": report_status
                    }
            }
        )


@app.route('/reports')
def get_reports():
    reports = get_conn().cursor().execute("SELECT * from public.report").fetchall()
    if (reports):
        return jsonify(reports)
    return jsonify(
        {
            "code": 404,
            "message": "no reports."
        }
    ), 404


def checkMsg(message):
    check = True
    categories = ['sexual', 'racist', 'vulgar']

    return check


if __name__ == '__main__':
    app.run(port=5005, debug=True)
