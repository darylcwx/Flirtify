from flask import Flask, jsonify
from flask_restful import Resource, Api
import random

app = Flask("DateAPI")
api = Api(app)

dates = {
    'prefFirstDate': 
    {'sporty': 
            ['go to the gym',
            'play tennis']
        ,
        'artistic':
            ['try painting',
            'go to the museum']
        ,
        'adventurous':
            ['go scuba diving',
            'go sky-diving']
        ,
        'animalLover':
            ['visit the zoo',
            'visit a dog cafe']
        ,
        'foody':
            ['visit a cafe',
            'try vietnamese food']
    }
}

class Date(Resource):
    def get(self):
        return dates
    
@app.route('/dateideas', methods=['GET'])
def getAllDates():
    return jsonify(dates)

@app.route('/dateidea/<string:pref>', methods=['GET'])    
def specificDates(pref):
    # based on pref, return a random idea
    if pref in dates["prefFirstDate"]:
        recos = dates["prefFirstDate"][pref]
        recoMax = len(recos)
        rando = random.randint(0,recoMax-1)

        return jsonify(recos[rando])

api.add_resource(Date, '/')

if __name__ == '__main__':
    app.run(port=5005, debug=True)
