from flask import Flask, request, jsonify
from flask_cors import CORS

import os, sys
import psycopg

import requests
from invokes import invoke_http

app = Flask(__name__)
CORS(app)

user_URL = 'http://localhost:5000/person'
message_URL = 'http://localhost:5001/message'
match_URL = 'http://localhost:5002/match'

@app.route("/add_report", methods=["POST"])
def add_report():
    if request.is_json:
        try:
            report = request.get_json()
            print("\nReceived a report in JSON:", report)

            # 1. add report into report database 
            conn_params = {
                'host':"flirtify-4040.6xw.cockroachlabs.cloud",
                'port':"26257",
                'dbname':"flirtify",
                'user':"jeremy",
                'password':"GvtUwDUhQOYrlDC7jEbblg",} 
            conn = psycopg.connect(**conn_params)
            cur = conn.cursor()

            cur.execute("INSERT INTO public.report (id, userid, category, message) VALUES (%s, %s, %s, %s, %s)")

            # 2. delete match 
            print('\n-----Invoking match microservice-----')
            match_result = invoke_http(match_URL, method='DEL', json=report) #change json
            print('match_result:', match_result)  

            reps = cur.execute("SELECT * from public.report where userid = %s")
            if len(reps) >= 5:
                # exceeded
                print('\n\n-----Invoking user microservice-----')
                user_result = invoke_http(user_URL, method="DEL", json=report) #change json
                print('user_result:', user_result)   
                report_result = "Number of reports exceeded 5, user deleted"

            else:
                # havent exceed, increment by 1
                print('\n\n-----Invoking user microservice-----')
                user_result = invoke_http(user_URL, method="PUT", json=report) #change json
                print('user_result:', user_result) 
                report_result = "Number of reports increased by 1"

            conn.commit()


            result = {"code": 201,
                        "data": {
                            "report_result": report_result
                        }
                    }
            return jsonify(result), result["code"]

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            ex_str = str(e) + " at " + str(exc_type) + ": " + fname + ": line " + str(exc_tb.tb_lineno)
            print(ex_str)

            return jsonify({
                "code": 500,
                "message": "add_report.py internal error: " + ex_str
            }), 500

    return jsonify({
        "code": 400,
        "message": "Invalid JSON input: " + str(request.get_data())
    }), 400


if __name__ == '__main__':
    app.run(port=5005, debug=True)
