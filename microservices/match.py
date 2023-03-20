from pyexpat.errors import messages
from flask import Flask, jsonify, request, render_template, redirect, url_for
from cockroachdb.sqlalchemy import run_transaction
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, null
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import aliased
import requests
import json

app = Flask(__name__, template_folder='../templates')

# Configure the SQLAlchemy engine to use CockroachDB
engine = create_engine('cockroachdb://jeremy:GvtUwDUhQOYrlDC7jEbblg@flirtify-4040.6xw.cockroachlabs.cloud:26257/flirtify?sslmode=require')

# Create a SQLAlchemy session factory to manage database connections
Session = sessionmaker(bind=engine)

# Create a base class for database models
Base = declarative_base()

class Match(Base):
    __tablename__ = 'match'
    match_id = Column(Integer, primary_key=True, autoincrement=True)
    
    user_id1 = Column(Integer, nullable = False)
    user_id2 = Column(Integer, nullable = False)

    user1_match = Column(Boolean, nullable = True)
    user2_match = Column(Boolean, nullable = True)

    datePrefs = Column(ARRAY(String))
    dateIdea = Column(ARRAY(String))

    # dateMatch = Column(Date, nullable = True)

    def json(self):
        return {"match_id": self.match_id, "user_id1": self.user_id1, "user_id2": self.user_id2, "user1_match": self.user1_match, "user2_match": self.user2_match, "datePrefs": self.datePrefs, "dateIdea": self.dateIdea} #to include: "date":self.date

session = Session()

# Create table
# Base.metadata.create_all(engine)


# retrieve all matches
@app.route("/match")
def get_all():
    matches = session.query(Match).all()
    if len(matches):
        return jsonify(
            {
                "code": 200,
                "data": {
                    "matches": [match.json() for match in matches]
                }
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "You have no matches."
        }
    ), 404

# specific match by match_id
@app.route("/match/<string:match_id>")
def find_by_match_id(match_id):
    match = session.query(Match).filter_by(match_id=match_id).first()

    if match:
        return jsonify(
            {
                "code": 200,
                "data": match.json()
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "Match not found."
        }
    ), 404

# return successful matches by user id
@app.route("/successful_match/<string:user_id>")
def find_successful_matches(user_id):
    #filter out by userid
    m1 = session.query(Match).filter(Match.user_id1 == user_id)
    m2 = session.query(Match).filter(Match.user_id2 == user_id)

    #all matches by userid
    matches = m1.union(m2).filter(Match.user1_match == "true", Match.user2_match).all()

    # if matches means swiped - or have created match
    if matches:
        #filter out successful matches
        ##### COMPUTATIONALLY TAXING ###############
        # then we populate the datepref and dateidea

        for match in matches:
            # populate dates with date ideas and stuff
            matchid = match.match_id

            # only if no null, then we start populating
            if ((match.datePrefs == null) or (match.dateIdea == null)):
                try:
                    requests.post("http://localhost:5002/populate_dateprefs/{}".format(matchid))

                    try:
                        requests.post("http://localhost:5002/date_recommendation/{}".format(matchid))

                    except:
                        return jsonify(
                            {
                                "code": 500,
                                "message": "An error occurred populating the date recommendation. Please try again."
                            }
                        ), 500

                except:
                    return jsonify(
                        {
                            "code": 500,
                            "message": "An error occurred creating the date preference. Please try again."
                        }
                    ), 500

        # else return
        return jsonify(
            {
                "code": 200,
                "data": [match.json() for match in matches]
            }        
        )
    else:
        return jsonify(
        {
            "code": 404,
            "message": "Match not found."
        }
    ), 404


# get all matches for a unique user
@app.route("/match/user/<int:user_id>")
def find_matches_by_user_id(user_id):
    m1 = session.query(Match).filter(Match.user_id1 == user_id)
    m2 = session.query(Match).filter(Match.user_id2 == user_id)
    matches = m1.union(m2).all()


    if matches:
        return jsonify(
            {
                "code": 200,
                "data": [match.json() for match in matches]
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "Matches not found for user_id: {}".format(user_id)
        }
    ), 404


@app.route("/create_match", methods=['POST'])
def create_match():
    
    #hidden form data 

    #person deciding
    user_chooser_id = request.form['user_chooser_id']

    #person that is recommended
    user_suggested_id = request.form['user_suggested_id']

    #yes or no decision
    decision_form = request.form['decision']
    if decision_form == "1" or decision_form == 1:
        decision = True
    else:
        decision = False

    chooser_as_user2_match = session.query(Match).filter(Match.user_id2 == user_chooser_id).first()
    
    suggested_as_user1_match = session.query(Match).filter(Match.user_id1 == user_suggested_id).first()

    #checking if match with this 2 users exists
    if (chooser_as_user2_match and suggested_as_user1_match):
        chooser_as_user2_match.user2_match = decision
        
        try:
            # # add a date field here
            # chooser_as_user2_match.dateMatch = date.today.strftime('%d/%m/%Y')

            # # can also populate the datePref and dateIdea here
            # # call the two urls

            session.commit()

            return jsonify(
                {
                    "code": 201,
                    "data": chooser_as_user2_match.json()
                }
            ), 201

        except:
            return jsonify(
                {
                    "code": 500,
                    "message": "An error occurred updating the match. Please try again."
                }
            ), 500
    else:
        new_match = Match(
            user_id1 = user_chooser_id,
            user_id2 = user_suggested_id,
            user1_match = bool(decision)
        )
        try:
            session.add(new_match)
            session.commit()

            return jsonify(
                {
                    "code": 201,
                    "data": new_match.json()
                }
            ), 201

        except:
            return jsonify(
                {
                    "code": 500,
                    "message": "An error occurred creating the match. Please try again."
                }
            ), 500

# DELETE MATCH - In event of banning
@app.route("/match/<string:match_id>", methods=['DELETE'])
def delete_match(match_id):
    match = session.query(Match).filter_by(match_id=match_id).first()
    if match:
        session.delete(match)
        session.commit()
        return jsonify(
            {
                "code": 200,
                "data": {
                    "match_id": match_id
                },
                "message": "Match successfully deleted."
            }
        )
    return jsonify(
        {
            "code": 404,
            "data": {
                "match_id": match_id
            },
            "message": "Match not found."
        }
    ), 404

# check if match match
@app.route('/check_match', methods=['POST'])
def check_match():
    data = request.get_json()
    # Extract the attributes from the request JSON data
    user1_match = data['user1_match']
    user2_match = data['user2_match']
    # Check if the attributes are equal
    if user1_match == user2_match:
        result = True
    else:
        result = False
    # Return the result as a JSON response
    return jsonify({'result': result})


# new -- populate datePrefs
@app.route('/populate_dateprefs/<int:match_id>', methods=['POST'])
def populate_datepref(match_id):
    match = session.query(Match).filter_by(match_id=match_id).first()

    user1 = match.user_id1
    user2 = match.user_id2

    dateprefs = []
    
    for userid in [user1, user2]:
        user_data = requests.get("http://localhost:26257/user/{}".format(userid))
       
        if user_data.status_code == 200 and 'application/json' in user_data.headers.get('content-type'):
            json_data = user_data.json()['data']

            for variable in json_data:
                # Check if the "name" key is present in the dictionary
                if variable == 'desiredfirstdate':
                    dateprefs.append(json_data['desiredfirstdate'])
        else:
            return jsonify(
                {
                    "code": 404,
                    "message": "An error occurred creating the date preference. Date preference was not populated"
                }
            )

    if dateprefs != []:
        try:
            match.datePrefs = dateprefs
            # session.query(Match).filter_by(match_id=match_id).first().update({'datePrefs': dateprefs})
            session.commit()

            return jsonify(
                {
                    "code": 201,
                    "data": match.json()
                }
            ), 201

        except:
            return jsonify(
                {
                    "code": 500,
                    "message": "An error occurred creating the date preference. Please try again."
                }
            ), 500

# new -- populate datePrefs end


@app.route('/date_recommendation/<int:match_id>', methods=['POST'])
def populate_dateIdea(match_id):
    match = session.query(Match).filter_by(match_id=match_id).first()

    datePrefs = match.datePrefs    
    dateIdeas = []

    for prefDate in datePrefs:
        # send a formdata for each of the match
        url = f"http://localhost:5005/dateidea/{prefDate}"
        response = requests.get(url)

        # Handle the API response
        if response.status_code == 200:
            # Extract the idea from the JSON response
            idea = response.json()

            # Append the idea to the list of date ideas
            dateIdeas.append(idea)
        else:
            # Handle the error
            return jsonify(
                {
                    "message": "There was an error generating the date idea."
                }
            ), 404
    
        try:
            # Return the success message with the populated date ideas
            match.dateIdea = dateIdeas
            # session.query(Match).filter_by(match_id=match_id).first().update({'datePrefs': dateprefs})
            session.commit()

            return jsonify(
                {
                    "code": 201,
                    "data": match.json()
                }
            ), 201

        except:
            return jsonify(
                {
                    "code": 500,
                    "message": "An error occurred creating the date idea. Please try again."
                }
            ), 500
        
@app.context_processor
def inject_navbar():
    return dict(navbar="navbar.html")

if __name__ == '__main__':
    app.run(port=5002, debug=True)
