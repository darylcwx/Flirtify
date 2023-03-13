from flask import Flask, request, jsonify
from flask_cors import CORS

import os, sys

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

            result = processReport(report)
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


def processReport(report):
    # 2. delete match 
    print('\n-----Invoking match microservice-----')
    match_result = invoke_http(match_URL, method='DEL', json=report)
    print('match_result:', match_result)


    # 3. get reported user details
    print('\n\n-----Invoking user microservice-----')
    user_result = invoke_http(user_URL, method="GET", json=report)
    print('user_result:', user_result)
    # check if no. of reports exceed 5 
    num = 3 #temp

    if num >= 5:
        # exceeded
        print('\n\n-----Invoking user microservice-----')
        user_result = invoke_http(user_URL, method="DEL", json=report)
        print('user_result:', user_result)   

    else:
        # havent exceed, increment by 1
        print('\n\n-----Invoking user microservice-----')
        user_result = invoke_http(user_URL, method="PUT", json=report)
        print('user_result:', user_result)        
    

    # 4. invoke message microservice for?
    print('\n\n-----Invoking message microservice-----')
    message_result = invoke_http(message_URL, method="GET", json=report)
    print('message_result:', message_result)


    # 5. Send new order to shipping
    # Invoke the shipping record microservice
    print('\n\n-----Invoking shipping_record microservice-----')
    shipping_result = invoke_http(
        shipping_record_URL, method="POST", json=order_result['data'])
    print("shipping_result:", shipping_result, '\n')

    # Check the shipping result;
    # if a failure, send it to the error microservice.
    code = shipping_result["code"]
    if code not in range(200, 300):


    # Inform the error microservice
        print('\n\n-----Invoking error microservice as shipping fails-----')
        invoke_http(error_URL, method="POST", json=shipping_result)
        print("Shipping status ({:d}) sent to the error microservice:".format(
            code), shipping_result)

    # 7. Return error
        return {
            "code": 400,
            "data": {
                "order_result": order_result,
                "shipping_result": shipping_result
            },
            "message": "Simulated shipping record error sent for error handling."
        }


    # 7. Return created order, shipping record
    return {
        "code": 201,
        "data": {
            "order_result": order_result,
            "shipping_result": shipping_result
        }

    }


if __name__ == '__main__':
    app.run(port=5005, debug=True)
