from flask import Flask, jsonify, request, render_template, redirect, url_for, session
from flask_cors import CORS
from invokes import invoke_http
import requests
import json
import os
from datetime import datetime
import random

app = Flask(__name__, template_folder='../templates')
CORS(app)

# https://rapidapi.com/ajith/api/love-calculator/
# remove hard code when live https://rapidapi.com/xtraszone-api-xtraszone-api-default/api/real-love-calculator
# payment got some issues https://rapidapi.com/AstroMatcherAPI/api/astro-matcher-api

# For testing
#http://localhost:7000/get_compatibility/849412270219001857/3

#====================================================================
#====================================================================
import pika
RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST', 'localhost')

#hostname = "localhost"
port = 5672
connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, port=port))
channel = connection.channel()

# Declare Exchange
channel.exchange_declare(exchange='profiles_topic', exchange_type="topic", durable=True)

# Declare and bind Queue
channel.queue_declare(queue='profiles', durable=True)
channel.queue_bind(exchange='profiles_topic', queue='profiles') 



#====================================================================
#====================================================================

@app.route("/get_compatibility/<string:user1id>/<int:num>", methods=['GET'])
def get_compatibility(user1id, num):
    user_URL = "http://localhost:26257/user"
    #====================================================================
    # ACCESS USER MICROSERVICE TO GET USER OBJECTS
    user1 = invoke_http(user_URL + "/" + user1id, method='GET')
    users = invoke_http(user_URL, method='GET')
    if user1["code"] == 500 or users["code"] == 500:
        return user1
    elif user1["code"] == 404 or users["code"] == 404:
        return jsonify(
            {
                "code": 404,
                "message": "User(s) not found."
            }
        ), 404
    user1 = user1["data"]
    users = users["data"]["users"]
    random.shuffle(users)
    #====================================================================
    # user different gender and not already queued.
    try:
        result = { "code": "201", "data" : []}
        # forAMQP = { "code": "201", "data" : []}
        queued = []
        for user in users:
            print(user["firstname"])
            if len(queued) == num:
                break
            if user["id"] != user1["id"] and user["gender"] != user1["gender"] and user not in queued:
                user2 = user
                queued.append(user)
                res = processGetCompatibility(user1, user2)
                result["data"].append(res)

                # splitting up result, return 1 now, send the rest to AMQP
                # if len(queued) == 0:
                #    result["data"].append(res)
                # else:
                #     forAMQP = { "code": "201", "data" : []}
                #     forAMQP["data"].append(res)
                # break

    except Exception as e:
        result = { "code": "500", "message": "Internal server error occurred. Please try again later."}
    
    # return 1, the rest AMQP (need remove from above result["data"])
    if num > 1:
        # change result in body to forAMQP
        channel.basic_publish(exchange='profiles_topic', routing_key='', body=json.dumps(result), properties=pika.BasicProperties(delivery_mode = 2))

    # for now,
    return jsonify(result)
    
    
    #====================================================================
    #====================================================================

def processGetCompatibility(user1, user2):
    name1 = user1["firstname"] + " " + user1["lastname"] 
    name2 = user2["firstname"]  + " " + user2["lastname"] 
    bd1 = user1["birthdate"]
    bd2 = user2["birthdate"]
    mbti1 = user1["mbti"]
    mbti2 = user2["mbti"]
    pref1 = user1["preferences"]
    pref2 = user2["preferences"]
    
    print("==================")
    print("==================")
    print("==================")
    print(user1)
    print("==================")
    print(user2)
    

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
    # free api, but limited calls. can't use bc payment method issue, but by right the returned dict is hardcoded below
    print("API 3: " + response.text) 
    dict = {"type": "ok","result": {"attraction": 62,"emotion": 66,"mental": 64,"endurability": 81,"lifePath": 50,"children": 66,"overall": 70}
    }
    result3 = dict["result"]["overall"]

    # 4. Algorithm defined here
    if "NF" in mbti1 and "SJ" in mbti2 or "NF" in mbti2 and "SJ" in mbti1:
        mbti = 80
    elif "STJ" in mbti1 and "SFJ" in mbti2 or "STJ" in mbti2 and "SFJ" in mbti1 or "NF" in mbti1 and "NF" in mbti2:
        mbti = 70
    else:
        mbti = 60

    maxPref = max(len(pref1), len(pref2))
    prefCount = 0
    for i in pref1:
        if i in pref2:
            prefCount += 1
    prefScore = min(50, prefCount/maxPref * 100)

    compatibility_result = str(round(((int(result1) + int(result2) + int(result3) + prefScore) + mbti) / 5,2)) + "%"
    print("Compat result = " + compatibility_result)
    return {
        "code": 201,
        "data": {
            "user1": user1,
            "user2": user2,
            "compatibility_result": compatibility_result
        }
    }

if __name__ == "__main__":
    print("This is flask " + os.path.basename(__file__) +
          " for getting compatibility...")
    app.run(host="0.0.0.0", port=7000, debug=True)