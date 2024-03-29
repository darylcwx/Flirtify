from flask import Flask, jsonify
from flask_cors import CORS
from invokes import invoke_http
import pika
import requests
import json
import os, sys
from datetime import datetime
import random
import asyncio

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.config['SECRET_KEY'] = 'flirtify_esd_micro'
app.config['SESSION_COOKIE_DOMAIN'] = '127.0.0.1'
app.config['SESSION_COOKIE_PATH'] = '/'
CORS(app)

# https://rapidapi.com/ajith/api/love-calculator/
# remove hard code when live https://rapidapi.com/xtraszone-api-xtraszone-api-default/api/real-love-calculator
# payment got some issues https://rapidapi.com/AstroMatcherAPI/api/astro-matcher-api

# For testing
#http://localhost:7000/get_queue/849811382189850625/3

#====================================================================
#====================================================================


#====================================================================
#====================================================================

def callback(ch, method, properties, body):
    print(jsonify(body.decode('utf-8')))

@app.route('/get_queue_msg', methods=['GET'])
def get_queue_msg():
    connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
    channel = connection.channel()

    channel.queue_declare(queue='profiles', durable=True)

    method_frame, _, body = channel.basic_get(queue='profiles', auto_ack=True)
    if method_frame:
        data = json.loads(body)
        return jsonify(data)
    else:
        return jsonify(
            {
                'error': 'No message found.'
            }
        ), 404

@app.route("/get_queue/<string:user1id>/<int:num>", methods=['GET'])
def get_queue(user1id, num):
    return get_compatibility(user1id, num)

@app.route("/get_queue_async/<string:user1id>/<int:num>", methods=['GET'])
async def get_queue_async(user1id, num):
    await asyncio.sleep(0)
    result = get_compatibility(user1id, num) #response object
    json_result = result.get_json() #json object
    try:
        RABBITMQ_HOST = os.environ.get('esd-rabbitmq', 'rabbitmq')
        port = 5672
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, port=port))
        channel = connection.channel()

        # Declare Exchange
        channel.exchange_declare(exchange='profiles_direct', exchange_type="direct", durable=True)

        # Declare and bind Queue 
        channel.queue_declare(queue='profiles', durable=True)
        channel.queue_bind(exchange='profiles_direct', queue='profiles') 
        for current_json_result in json_result['data']:
            channel.basic_publish(exchange='profiles_direct', routing_key='profiles', body=json.dumps(current_json_result), properties=pika.BasicProperties(delivery_mode = 2))
    except:
        return jsonify(
            { 
                "code": 500, 
                "message": "Unable to connect to RabbitMQ queue='profiles' in exchange='profiles_direct'"
            }
        ), 200

    return jsonify(
            { 
                "code": 200, 
                "message": "Returned result to RabbitMQ queue='profiles' in exchange='profiles_direct'"
            }
        ), 200

def get_compatibility(user1id, num):
    user_URL = "http://user:26257/user"
    #====================================================================
    # ACCESS USER MICROSERVICE TO GET USER OBJECTS
    user1 = invoke_http(user_URL + "/" + user1id, method='GET')
    users = invoke_http(user_URL, method='GET')
    if user1["code"] == 404 or users["code"] == 404:
        return jsonify(
            {
                "code": 404,
                "message": "User(s) not found."
            }
        ), 404
    elif user1["code"] not in range(200, 300):
        return jsonify(
            {
                "code": 500,
                "data": user1,
                "message": "Internal server error."
            }
        ), 500
    elif users["code"] not in range(200, 300):
        return jsonify(
            {
                "code": 500,
                "data": users,
                "message": "Internal server error."
            }
        ), 500
    user1 = user1["data"]
    users = users["data"]["users"]
    random.shuffle(users)
    #====================================================================
    try:
        result = { "code": "200", "data" : []}
        queued = []
        for user in users:
            if len(queued) == num:
                break
            if user["id"] != user1["id"] and user["gender"] != user1["gender"] and user not in queued:
                user2 = user
                queued.append(user)
                res = processCompatibility(user1, user2)
                if res["code"] not in range(200,300):
                    return jsonify(
                        {
                            "code": 400,
                            "message": "Bad request. Please check that APIs are available and working."
                        }
                    )
                else:
                    res['data']['user1']['id'] = str(res['data']['user1']['id'])
                    res['data']['user2']['id'] = str(res['data']['user2']['id'])
                    result["data"].append(res)

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        ex_str = str(e) + " at " + str(exc_type) + ": " + fname + ": line " + str(exc_tb.tb_lineno)
        print(ex_str)
        result = { "code": "500", 
                  "message": "get_queue.py internal error: " + ex_str
                  }

    return jsonify(result)
    #====================================================================
    #===================================================================

def processCompatibility(user1, user2):
    name1 = user1["firstname"] + " " + user1["lastname"] 
    name2 = user2["firstname"]  + " " + user2["lastname"] 
    bd1 = user1["birthdate"]
    bd2 = user2["birthdate"]
    mbti1 = user1["mbti"]
    mbti2 = user2["mbti"]
    pref1 = user1["preferences"]
    pref2 = user2["preferences"]
    
    # print("==================")
    # print("==================")
    # print("==================")
    # print(user1)
    # print("==================")
    # print(user2)
    
    # =================================================================================
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
    if "percentage" in dict:
        result1 = int(dict["percentage"])
    else:
        result1= dict["message"]
    # =================================================================================
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
    if "overall" in dict:
        result2 = int(dict["overall"])
    else:
        result2 = dict["message"]
    # placeholder hard code in case API not working
    result2 = 78
    # =================================================================================
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
    dict = json.loads(response.text)
    dict = {"type": "ok","result": {"attraction": 62,"emotion": 66,"mental": 64,"endurability": 81,"lifePath": 50,"children": 66,"overall": 70}}
    if "result" in dict:
        result3 = int(dict["result"]["overall"])
    else:
        result3 = dict["message"]
    # =================================================================================
    # 4. Algorithm defined here
    if "NF" in mbti1 and "SJ" in mbti2 or "NF" in mbti2 and "SJ" in mbti1:
        mbti = 90
    elif "STJ" in mbti1 and "SFJ" in mbti2 or "STJ" in mbti2 and "SFJ" in mbti1 or "NF" in mbti1 and "NF" in mbti2:
        mbti = 80
    else:
        mbti = 70

    maxPref = max(len(pref1), len(pref2))
    minPref = min(len(pref1), len(pref2))
    prefCount = 0
    for i in pref1:
        if i in pref2:
            prefCount += 1
    prefScore = 50 + prefCount/minPref * 100

    try:
        compatibility_result = str(round((result1 + result2 + result3 + prefScore + mbti) / 5,2)) + "%"
        return {
        "code": 200,
        "data": {
            "user1": user1,
            "user2": user2,
            "compatibility_result": compatibility_result
        }
    }
    except:
        return {
            "code": 400,
            "message": "Bad request. Please check that APIs are available and working."
        }

if __name__ == "__main__":
    print("This is flask " + os.path.basename(__file__) +
          " for getting queue and compatibility...")
    loop = asyncio.get_event_loop()
    loop.create_task(app.run(host="0.0.0.0", port=7100, debug=True))
    loop.run_forever()