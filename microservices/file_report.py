from flask import Flask, jsonify, request, render_template, redirect, url_for, session
from flask_cors import CORS
# import psycopg
import requests
from invokes import invoke_http
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import json as jsonnn
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey
import requests


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

Base = declarative_base()

# class Report(db.Model):
#     __tablename__ = 'report'
    
#     userid = db.Column(db.Integer, primary_key=True)
#     otherid = db.Column(db.Integer, primary_key=True)
#     matchid = db.Column(db.Integer)
    
#     def __init__(self, userid, otherid, matchid):
#         self.userid = userid
#         self.otherid = otherid

# def get_conn():
#     conn = psycopg.connect(**conn_params, autocommit=True)
#     return conn

# def run_sql(sql):
#     with get_conn() as txn:
#         txn.execute(sql)
        
# def json(info):
#     result = {'info':info[0]}
#     result = {"userid":info[0], "otherid":info[1], "matchid":info[2]}
#     return result

class Report(Base):
    __tablename__ = 'report'

    userid = Column(Integer, primary_key=True)
    otherid = Column(Integer, primary_key=True)
    matchid = Column(Integer)

    def __init__(self, userid, otherid, matchid):
        self.userid = userid
        self.otherid = otherid
        self.matchid = matchid

    def json(self):
        result = {
            'userid'  : self.userid,
            'otherid' : self.otherid,
            'matchid' : self.matchid
        }
        return result

session_db = Session()

user_URL = 'http://user:26257/user/'
message_URL = 'http://messages:5010/api/get_all_messages/'
match_URL = 'http://match:5002/match/'

@app.route("/add_report/<string:userid>/<string:otherid>/<string:matchid>")
def add_report(userid, otherid, matchid):
    # print("\nReceived a report from userID:", userid, " reporting userID:", otherid, "\n matchid:", matchid)

    # check messages
    result = checkMsg(otherid, matchid)
    if result == 'api failed to check messages':
        # delete match 
        match_result = invoke_http(match_URL + matchid, method='DELETE', json=None) 
        print('match_result:', match_result)  

        return jsonify(
            {
                "code": 500,
                "data": {
                    "status": 'Check user message failed. Please try again later.'
                    }
            }
        )
    
    elif result == 'no profanities detected':
        # delete match 
        match_result = invoke_http(match_URL + matchid, method='DELETE', json=None) 
        print('match_result:', match_result)  

        return jsonify(
            {
                "code": 200,
                "data": {
                    "status": 'User message did not include any profanities. Report not added.'
                    }
            }
        )

    # add report into database
    new_report = Report(
        userid = userid,
        otherid = otherid,
        matchid = matchid
        )
    
    # delete match 
    match_result = invoke_http(match_URL + matchid, method='DELETE', json=None) 
    print('match_result:', match_result)  
    
    try:
        session_db.add(new_report)
        session_db.commit()
        
        reps = session_db.query(Report).filter(Report.otherid == otherid).all()

        if len(reps) >= 5:
            print('\n\n-----Invoking user microservice-----')
            user_result = invoke_http(user_URL + otherid , method="DELETE", json=None) 
            print('user_result:', user_result)   

            try:
                requests.post("http://match:5002/match/ban/{}".format(otherid))
                report_status = "Number of reports exceeded 5, user deleted"

            except:
                return jsonify(
                    {
                        "code": 502,
                        "data": "An error occurred removing all matches related to reported user. Please try again."
                    }
                ), 502
            
        else:
            report_status = "Number of reports increased by 1, total reports: " + str(len(reps)+1)
        
    except Exception as e:
        session_db.rollback()
        app.logger.error(f"Error committing session: {str(e)}")
        return jsonify(
            {
                "code": 500,
                "message": "There was an error sending your report. Please try again."
            }
        ) 
        

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
#     result = []
    
#     for report in reports:
#         result.append(json(report))

#     if (reports):
#         return result
    
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

    if text.strip() == '':
        return 'no profanities detected'

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
    app.run(host='0.0.0.0', port=5015, debug=True)
