from pyexpat.errors import messages
from flask import Flask, jsonify, request, render_template, redirect, url_for
from cockroachdb.sqlalchemy import run_transaction
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/persons'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Configure the SQLAlchemy engine to use CockroachDB
engine = create_engine('cockroachdb://jeremy:GvtUwDUhQOYrlDC7jEbblg@flirtify-4040.6xw.cockroachlabs.cloud:26257/flirtify?sslmode=require')

# Create a SQLAlchemy session factory to manage database connections
Session = sessionmaker(bind=engine)

class Match(db.Model):
    __tablename__ = 'match'
    match_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    user_id1 = db.Column(db.Integer, nullable = False)
    user_id2 = db.Column(db.Integer, nullable = False)

    user1_match = db.Column(db.Boolean, nullable = True)
    user2_match = db.Column(db.Boolean, nullable = True)

    dateMatch = db.Column(db.Boolean, nullable = True)
    dateIdea = db.Column(db.ARRAY(db.String))

    def json(self):
        return {"match_id": self.match_id, "user_id1": self.user_id1, "user_id2": self.user_id2, "user1_match": self.user1_match, "user2_match": self.user2_match, "dateMatch": self.dateMatch, "dateIdea": self.dateIdea}

session = Session()

# Create table
# Base.metadata.create_all(engine)


# retrieve all matches
@app.route("/match")
def get_all():
    matches = Match.query.all()
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

# specific match
# problem with this is that it might return a match that has not been verified to be [yes,yes] yet
@app.route("/match/<string:match_id>")
def find_by_match_id(match_id):
    match = Match.query.filter_by(match_id=match_id).first()
    if match_id:
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

# create match
@app.route("/match/<string:match_id>", methods=['POST'])
def create_match(match_id):

    # # SCENARIO 1: just prevent user from creating new match
    # if (Match.query.filter_by(match_id=match_id).first()):
    #     return jsonify(
    #         {
    #             "code": 400,
    #             "data": {
    #                 "match_id": match_id
    #             },
    #             "message": "You can only like once"
    #         }
    #     ), 400

    # SCENARIO 2: Users have yet to like each other yet. So there will be Yes, null for example. But they will still be engaging with the same Match_id
    match = Match.query.filter_by(match_id=match_id).first()
    if match:
        match = request.get_json()
        # potentially fucked up this part. 
        if match['match_id']:
            match.match_id = match['match_id']
        db.session.commit()

        return jsonify(
            {
                "code": 200,
                "data": match.json()
            }
        )

    data = request.get_json()
    match = Match(match_id, **data) #**data is a "common idiom" that allows an arbitrary number of arguments to a function. in this case, all attributes received from request is sent.

    try:
        db.session.add(match_id)
        db.session.commit()
    except:
        return jsonify(
            {
                "code": 500,
                "data": {
                    "match_id": match_id
                },
                "message": "An error occurred creating the match. Please try again."
            }
        ), 500


    return jsonify(
        {
            "code": 201,
            "data": match.json()
        }
    ), 201

# DELETE MATCH - In event of banning
@app.route("/match/<string:match_id>", methods=['DELETE'])
def delete_match(match_id):
    match = Match.query.filter_by(match_id=match_id).first()
    if match:
        db.session.delete(match)
        db.session.commit()
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

# check if date match

# NEEDS WORK
# Question: How to pull from user db?? How to then validate?


# @app.route('/check_match', methods=['POST'])
# def check_match():
#     data = request.get_json()
#     # Extract the attributes from the request JSON data
#     user1_match = data['user1_match']
#     user2_match = data['user2_match']
#     # Check if the attributes are equal
#     if user1_match == user2_match:
#         result = True
#     else:
#         result = False
#     # Return the result as a JSON response
#     return jsonify({'result': result})



if __name__ == '__main__':
    app.run(port=5002, debug=True)
