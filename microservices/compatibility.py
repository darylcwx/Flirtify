from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import pika
import json
import psycopg
import os

app = Flask(__name__)
CORS(app)

# https://rapidapi.com/ajith/api/love-calculator/
# https://rapidapi.com/xtraszone-api-xtraszone-api-default/api/real-love-calculator
# payment got some issues https://rapidapi.com/AstroMatcherAPI/api/astro-matcher-api


compatibility_URL = "http://localhost:5000/compatibility"
user_URL = "http://localhost:5001/user"

@app.route("/get_compatibility/<string:user1>", methods=['GET'])
def get_compatibility(user1id):
    conn_params = {
        'host':"flirtify-4040.6xw.cockroachlabs.cloud",
        'port':"26257",
        'dbname':"flirtify",
        'user':"jeremy",
        'password':"GvtUwDUhQOYrlDC7jEbblg",} 
    conn = psycopg.connect(**conn_params)
    cur = conn.cursor()

    # Fetch self
    cur.execute("SELECT * FROM public.users WHERE id = {user1id}")
    user1 = cur.fetchone()
    print(user1)

    # Fetch random user
    cur.execute("SELECT * from public.users WHERE gender != 'M' ORDER BY RANDOM() LIMIT 1")
    user2 = cur.fetchone()
    print(user2)

    
    #print("\nReceived a compatibility request in JSON:", users)
    result = processGetCompatibility(user1, user2)
    return jsonify(result), result["code"]

        # except Exception as e:
        #     # Unexpected error in code
        #     exc_type, exc_obj, exc_tb = sys.exc_info()
        #     fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        #     ex_str = str(e) + " at " + str(exc_type) + ": " + fname + ": line " + str(exc_tb.tb_lineno)
        #     print(ex_str)

        #     return jsonify({
        #         "code": 500,
        #         "message": "compatibility.py internal error: " + ex_str
        #     }), 500

    # if reached here, not a JSON request.
    # return jsonify({
    #     "code": 400,
    #     "message": "Invalid JSON input: " + str(request.get_data())
    # }), 400


def processGetCompatibility(user1, user2):
    u1name = user1[1] + " " + user2[1]
    u2name = user2[1] + " " + user2[2]
    u1BD = user1[4].strftime("%Y-%m-%d")
    u2BD = user2[4].strftime("%Y-%m-%d")
    # The compatibility algorithm is located here

    # 1. Love Calculator API from RapidAPI:
    url = "https://love-calculator.p.rapidapi.com/getPercentage"
    querystring = {"fname": user1[1],"sname": user2[1]}
    headers = {
        "X-RapidAPI-Key": "bdcae462fbmsh86b457452ab2afbp1b75cejsn641122d979a5",
        "X-RapidAPI-Host": "love-calculator.p.rapidapi.com"
    }
    response = requests.request("GET", url, headers=headers, params=querystring)
    print(response.text)
    dict = json.loads(response.text)
    result1 = dict["percentage"]

    # 2. Real Love Calculator API from RapidAPI:
    url = "https://real-love-calculator.p.rapidapi.com/"
    params = {"male": {"name": u1name, "dob": u1BD},
              "female": {"name": u2name,"dob": u2BD}}
    headers = {
        "content-type": "application/json",
        "X-RapidAPI-Key": "bdcae462fbmsh86b457452ab2afbp1b75cejsn641122d979a5",
        "X-RapidAPI-Host": "real-love-calculator.p.rapidapi.com"
    }
    response = requests.request("POST", url, json=params,headers=headers)
    print(response.text)
    dict = json.loads(response.text)
    #result2 = dict["overall"]
    result2 = 78


    # 3. Astro Matcher API from RapidAPI: but it's not working rapidAPI can't accept my payment method
    url = "https://astro-matcher-api.p.rapidapi.com/match2"
    lat = 1.3649170000000002
    long = 103.82287200000002
    u1y, u1m, u1d = u1BD.split("-")
    u2y, u2m, u2d = u2BD.split("-")
    querystring = {
            "a": f'{{ "year": {u1y}, "month": {u1m}, "day": {u1d}, "hour": 0, "minute": 0, "second": 0, "latitude": {lat}, "longitude": {long} }}',
            "b": f'{{ "year": {u2y}, "month": {u2m}, "day": {u2d}, "hour": 0, "minute": 0, "second": 0, "latitude": {lat}, "longitude": {long} }}'
            }
    headers = {
        "X-RapidAPI-Key": "bdcae462fbmsh86b457452ab2afbp1b75cejsn641122d979a5",
        "X-RapidAPI-Host": "astro-matcher-api.p.rapidapi.com"
    }
    response = requests.request("GET", url, headers=headers, params=querystring)
    print(response.text) # payment method issue, but returned dict is as below
    dict = {"type": "ok","result": {"attraction": 62,"emotion": 66,"mental": 64,"endurability": 81,"lifePath": 50,"children": 66,"overall": 70}
    }
    result3 = dict["result"]["overall"]

    # 4. Algorithm defined here
    compatibility_result = str(round((int(result1) + int(result2) + int(result3)) / 3,2)) + "%"
    return {
        "code": 201,
        "data": {
            "compatibility_result": compatibility_result
        }
    }


if __name__ == "__main__":
    print("This is flask " + os.path.basename(__file__) +
          " for getting compatibility...")
    app.run(host="0.0.0.0", port=5100, debug=True)