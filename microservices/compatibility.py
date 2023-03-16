from flask import Flask, jsonify
from flask_cors import CORS
from invokes import invoke_http
import requests
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# https://rapidapi.com/ajith/api/love-calculator/
# remove hard code when live https://rapidapi.com/xtraszone-api-xtraszone-api-default/api/real-love-calculator
# payment got some issues https://rapidapi.com/AstroMatcherAPI/api/astro-matcher-api

@app.route("/get_compatibility/<string:user1id>/<string:user2id>", methods=['GET'])
def get_compatibility(user1id, user2id):
    user_URL = "http://localhost:26257/user"
    #====================================================================
    # ACCESS USER MICROSERVICE TO GET USER OBJECTS
    user1 = invoke_http(user_URL + "/" + user1id, method='GET')["data"]
    user2 = invoke_http(user_URL + "/" + user2id, method='GET')["data"]
    #====================================================================
    result = processGetCompatibility(user1, user2)
    return jsonify(result), result["code"]

def processGetCompatibility(user1, user2):
    name1 = user1["firstname"] + " " + user1["lastname"] 
    name2 = user2["firstname"]  + " " + user2["lastname"] 
    bd1 = user1["birthdate"]
    bd2 = user2["birthdate"]
    mbti1 = user1["mbti"]
    mbti2 = user2["mbti"]
    if "NF" in mbti1 and "SJ" in mbti2 or "NF" in mbti2 and "SJ" in mbti1:
        mbti = 75
    elif "STJ" in mbti1 and "SFJ" in mbti2 or "STJ" in mbti2 and "SFJ" in mbti1 or "NF" in mbti1 and "NF" in mbti2:
        mbti = 60
    else:
        mbti = 50
    print("==================")
    print(user1)
    print("==================")
    print(user2)
    print("==================")

    # 1. Love Calculator API from RapidAPI:
    url = "https://love-calculator.p.rapidapi.com/getPercentage"
    querystring = {"fname": name1,"sname": name2}
    headers = {
        "X-RapidAPI-Key": "bdcae462fbmsh86b457452ab2afbp1b75cejsn641122d979a5",
        "X-RapidAPI-Host": "love-calculator.p.rapidapi.com"
    }
    response = requests.request("GET", url, headers=headers, params=querystring)
    print("API 1: " + response.text)
    dict = json.loads(response.text)
    result1 = dict["percentage"]

    # 2. Real Love Calculator API from RapidAPI:
    url = "https://real-love-calculator.p.rapidapi.com/"
    params = {"male": {"name": name1, "dob": bd1},
              "female": {"name": name2,"dob": bd2}}
    headers = {
        "content-type": "application/json",
        "X-RapidAPI-Key": "bdcae462fbmsh86b457452ab2afbp1b75cejsn641122d979a5",
        "X-RapidAPI-Host": "real-love-calculator.p.rapidapi.com"
    }
    response = requests.request("POST", url, json=params,headers=headers)
    print("API 2: " + response.text)
    dict = json.loads(response.text)
    #result2 = dict["overall"]
    result2 = 78


    # 3. Astro Matcher API from RapidAPI: but it's not working rapidAPI can't accept my payment method
    url = "https://astro-matcher-api.p.rapidapi.com/match2"
    lat = 1.3649170000000002
    long = 103.82287200000002
    dFormat = "%a, %d %b %Y %H:%M:%S %Z"
    d1 = datetime.strptime(bd1, dFormat)
    d2 = datetime.strptime(bd2, dFormat)
    u1y, u1m, u1d, u1h, u1min, u1s = d1.year, d1.month, d1.day, d1.hour, d1.minute, d1.second
    u2y, u2m, u2d, u2h, u2min, u2s = d2.year, d2.month, d2.day, d2.hour, d2.minute, d2.second
    querystring = {
            "a": f'{{ "year": {u1y}, "month": {u1m}, "day": {u1d}, "hour": {u1h}, "minute": {u1min}, "second": {u1s}, "latitude": {lat}, "longitude": {long} }}',
            "b": f'{{ "year": {u2y}, "month": {u2m}, "day": {u2d}, "hour": {u2h}, "minute": {u2min}, "second": {u2s}, "latitude": {lat}, "longitude": {long} }}'
            }
    headers = {
        "X-RapidAPI-Key": "bdcae462fbmsh86b457452ab2afbp1b75cejsn641122d979a5",
        "X-RapidAPI-Host": "astro-matcher-api.p.rapidapi.com"
    }
    response = requests.request("GET", url, headers=headers, params=querystring)
    # payment method issue, but returned dict is as below
    print("API 3: " + response.text) 
    dict = {"type": "ok","result": {"attraction": 62,"emotion": 66,"mental": 64,"endurability": 81,"lifePath": 50,"children": 66,"overall": 70}
    }
    result3 = dict["result"]["overall"]

    # 4. Algorithm defined here
    compatibility_result = str(round(((int(result1) + int(result2) + int(result3)) + mbti) / 4,2)) + "%"
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