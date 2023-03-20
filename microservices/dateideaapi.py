from flask import Flask, jsonify
from flask_restful import Resource, Api
import random

app = Flask("DateAPI")
api = Api(app)

dates = {
    'prefFirstDate': 
    {'sporty': 
            ['Go to the gym with each other',
            'Play tennis with each other',
            'Go for a run at the park with each other!',
            'Go rock-climbing with each other',
            'Visit the trampoline park with each other',
            'Go for a hike at Bukit Timah Hill']
        ,
        'artistic':
            ['Try painting together',
            'Visit the Arts and Science museum',
            'Visit the Singapore Arts Museum',
            'Visit Artbox with each other']
        ,
        'adventurous':
            ['Go for a hike at Bukit Timah Hill',
            'Go rock-climbing with each other',
            "Visit the St John's Island with each other",
            "Visit Pulau Ubin with each other"]
        ,
        'animalLover':
            ['Visit the zoo',
            'Visit a dog cafe',
            'Visit Jurong Bird Park',
            'Volunteer at SPCA for a day']
        ,
        'food':
            ['Visit a cafe!',
            'Try Vietnamese food!',
            'Visit Artbox together',
            'Visit TipoSG together',
            'Have KBBQ together'
            ]
        ,
        'movies':
            ['Watch Everything All Together At Once together!',
            'Go on a Harry Potter movie marathon',
            'Watch the Avengers together',
            'Catch the latest movie at the cinema!']
        ,
        'indoors':
            ["Play a board game with each other at MindCafe",
             "Play Cards Against Humanity together",
             "Visit the library with each other",
             "Watch a movie at the cinema with each other",
             "Play video games with each other"]
        ,
        'gaming':
            ["Play Valorant with each other!",
             "Play League of Legends with each other!",
             "Play Overwatch 2 with each other!",
             "Play Teamfight Tactics with each other!"]
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
