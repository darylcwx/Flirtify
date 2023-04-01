from pyexpat.errors import messages
from flask import Flask, jsonify, request, render_template, redirect, url_for, session
from flask_cors import CORS
from cockroachdb.sqlalchemy import run_transaction
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, null
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Date
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import aliased
import requests
import json
from datetime import datetime

app = Flask(__name__, template_folder='../templates')
app.config['SECRET_KEY'] = 'flirtify_esd_micro'
app.config['SESSION_COOKIE_DOMAIN'] = '127.0.0.1'
app.config['SESSION_COOKIE_PATH'] = '/'
CORS(app)

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

    dateMatched = Column(Date, nullable = True)

    def json(self):
        return {"match_id": self.match_id, "user_id1": self.user_id1, "user_id2": self.user_id2, "user1_match": self.user1_match, "user2_match": self.user2_match, "datePrefs": self.datePrefs, "dateIdea": self.dateIdea, "dateMatched":self.dateMatched}

session = Session()

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/matches')
def matches():
    return render_template('matches.html')

@app.route('/chat')
def chat():
    return render_template('message.html')

#add table
@app.route('/add_table')
def add_table():
    # Create the database tables
    Base.metadata.create_all(engine)
    return "table created successfully"

#drop table
@app.route('/drop_table')
def drop_table():
    # Drop the table
    def drop_table(txn):
        txn.execute("DROP TABLE match")
    run_transaction(engine, drop_table)

    return 'Table dropped successfully.'

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
            "message": "There are no matches."
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
    matches = m1.union(m2).filter(Match.user1_match == "true", Match.user2_match == "true").all()

    # if matches means swiped - or have created match
    if matches:

        all_matches = []
        
        for match in matches:
            match_details = {
                'match_id'      : str(match.match_id),
                'dateIdea'      : match.dateIdea,
                'datePrefs'     : match.datePrefs,
                'user1_match'   : match.user1_match,
                'user2_match'   : match.user2_match,
                'user_id1'      : str(match.user_id1),
                'user_id2'      : str(match.user_id2),
                'dateMatched'   : match.dateMatched
                }
            all_matches.append(match_details)
                
        response = jsonify(
            {
                "code": 200,
                "data": all_matches
            }        
        )
    else:
        response = jsonify(
        {
            "code": 404,
            "message": "Match not found."
        }
        ), 404

    return response


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


# @app.route("/create_match", methods=['POST'])
# def create_match():
    
#     #hidden form data 

#     #person deciding
#     user_chooser_id = request.form['user_chooser_id']
#     print(user_chooser_id)
#     #person that is recommended
#     user_suggested_id = request.form['user_suggested_id']

#     #yes or no decision
#     decision_form = request.form['decision']
#     if decision_form == "1" or decision_form == 1:
#         decision = True
#     else:
#         decision = False

#     chooser_as_user2_match = session.query(Match).filter(Match.user_id2 == user_chooser_id).first()
    
#     suggested_as_user1_match = session.query(Match).filter(Match.user_id1 == user_suggested_id).first()

#     #checking if match with this 2 users exists
#     if (chooser_as_user2_match and suggested_as_user1_match):
#         chooser_as_user2_match.user2_match = decision
        
#         try:
#             # # add a date field here
#             # chooser_as_user2_match.dateMatch = date.today.strftime('%d/%m/%Y')

#             # # can also populate the datePref and dateIdea here
#             # # call the two urls

#             session.commit()
#             return jsonify(
#                 {
#                     "code": 201,
#                     "data": chooser_as_user2_match.json()
#                 }
#             ), 201

#         except:
#             return jsonify(
#                 {
#                     "code": 500,
#                     "message": "An error occurred updating the match. Please try again."
#                 }
#             ), 500
#     else:
#         new_match = Match(
#             user_id1 = user_chooser_id,
#             user_id2 = user_suggested_id,
#             user1_match = bool(decision)
#         )
#         try:
#             session.add(new_match)
#             session.commit()

#             return jsonify(
#                 {
#                     "code": 201,
#                     "data": new_match.json()
#                 }
#             ), 201

#         except:
#             return jsonify(
#                 {
#                     "code": 500,
#                     "message": "An error occurred creating the match. Please try again."
#                 }
#             ), 500


@app.route("/create_match/<string:user_chooser_id>/<string:user_suggested_id>/0", methods=['POST'])
def create_match_reject(user_chooser_id,user_suggested_id):

    chooser_as_user2_match = session.query(Match).filter(Match.user_id2 == user_chooser_id, Match.user_id1 == user_suggested_id).first()
    
    #checking if match with this 2 users exists
    if (chooser_as_user2_match):
        chooser_as_user2_match.user2_match = False
        
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
            user1_match = bool(False)
        )
        try:
            session.add(new_match)
            session.commit()

            return jsonify(
                {
                    "code": 200,
                    "data": new_match.json()
                }
            ), 200

        except:
            return jsonify(
                {
                    "code": 500,
                    "message": "An error occurred creating the match. Please try again."
                }
            ), 500

@app.route("/create_match/<string:user_chooser_id>/<string:user_suggested_id>/1", methods=['POST'])
def create_match_accept(user_chooser_id,user_suggested_id):

    chooser_as_user2_match = session.query(Match).filter(Match.user_id2 == user_chooser_id, Match.user_id1 == user_suggested_id).first()
    
    # suggested_as_user1_match = session.query(Match).filter(Match.user_id1 == user_suggested_id).first()

    #checking if match with this 2 users exists
    if (chooser_as_user2_match):
        chooser_as_user2_match.user2_match = True
        matchid = chooser_as_user2_match.match_id

        # only if both swiped right on each other then
        ifMatch = False
        if (chooser_as_user2_match.user2_match == True and chooser_as_user2_match.user1_match == True):
            ifMatch = True
            chooser_as_user2_match.dateMatched = datetime.today() #.strftime('%Y/%m/%d')

        try:
            session.commit()

            # only if match then populate datePref and dateIdea
            if ifMatch:                
 
                try:
                    requests.post("http://127.0.0.1:5002/populate_dateprefs/{}".format(matchid))

                    try:
                        requests.post("http://127.0.0.1:5002/date_recommendation/{}".format(matchid))

                    except:
                        return jsonify(
                            {
                                "code": 502,
                                "message": "An error occurred populating the date recommendation. Please try again."
                            }
                        ), 502

                except:
                    return jsonify(
                        {
                            "code": 501,
                            "message": "An error occurred creating the date preference. Please try again."
                        }
                    ), 501

            return jsonify(
                {
                    "code":     200,
                    "data":     chooser_as_user2_match.json(),
                    "matched":  ifMatch
                }
            ), 200


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
            user1_match = bool(True)
        )
        try:
            session.add(new_match)
            session.commit()

            return jsonify(
                {
                    "code":     201,
                    "data":     new_match.json(),
                    "matched":  False
                }
            ), 201

        except:
            return jsonify(
                {
                    "code": 503,
                    "message": "An error occurred creating the match. Please try again."
                }
            ), 503



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


@app.route("/match/ban/<string:user_id>", methods=['DELETE'])
def delete_all_matches(user_id):
    m1 = session.query(Match).filter(Match.user_id1 == user_id)
    m2 = session.query(Match).filter(Match.user_id2 == user_id)
    matches = m1.union(m2).all()

    if matches:
        for match in matches:
            session.delete(match)
        session.commit()
        return jsonify(
            {
                "code": 200,
                "message": "Deleted all matches related to user_id: {}".format(user_id)
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "Matches not found for user_id: {}".format(user_id)
        }
    ), 404


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
        
# @app.context_processor
# def inject_navbar():
#     return dict(navbar="navbar.html")

if __name__ == '__main__':
    app.run(port=5002, debug=True)
