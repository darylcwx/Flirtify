from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/persons'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
 
CORS(app)  

class Persons(db.Model):
    __tablename__ = 'person'

    id = db.Column(db.String(13), primary_key=True)
    firstname = db.Column(db.String(64), nullable=False)
    lastname = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(64), nullable=False)
    gender = db.Column(db.String(10), nullable=False)

    def __init__(self, id, firstname, lastname, email, gender):
        self.id = id
        self.firstname = firstname
        self.lastname = lastname
        self.email = email
        self.gender = gender

    def json(self):
        return {"id": self.id, "firstname": self.firstname, "lastname": self.lastname, "email": self.email, "gender": self.gender}


@app.route("/person")
def get_all():
    persons = Persons.query.all()
    if len(persons):
        return jsonify(
            {
                "code": 200,
                "data": {
                    "persons": [person.json() for person in persons]
                }
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "There are no users."
        }
    ), 404


@app.route("/person/<string:id>")
def find_by_id(id):
    person = Persons.query.filter_by(id=id).first()
    if person:
        return jsonify(
            {
                "code": 200,
                "data": person.json()
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "User not found."
        }
    ), 404


@app.route("/person/<string:id>", methods=['POST'])
def create_person(isbn13):
    if (Persons.query.filter_by(id=id).first()):
        return jsonify(
            {
                "code": 400,
                "data": {
                    "id": id
                },
                "message": "User already exists."
            }
        ), 400

    data = request.get_json()
    person = Persons(id, **data)

    try:
        db.session.add(person)
        db.session.commit()
    except:
        return jsonify(
            {
                "code": 500,
                "data": {
                    "id": id
                },
                "message": "An error occurred creating the user."
            }
        ), 500

    return jsonify(
        {
            "code": 201,
            "data": person.json()
        }
    ), 201


@app.route("/person/<string:id>", methods=['PUT'])
def update_person(id):
    person = Persons.query.filter_by(id=id).first()
    if person:
        data = request.get_json()
        if data['title']:
            person.title = data['title']
        db.session.commit()
        return jsonify(
            {
                "code": 200,
                "data": person.json()
            }
        )
    return jsonify(
        {
            "code": 404,
            "data": {
                "id": id
            },
            "message": "User not found."
        }
    ), 404


@app.route("/person/<string:id>", methods=['DELETE'])
def delete_person(id):
    person = Persons.query.filter_by(id=id).first()
    if person:
        db.session.delete(person)
        db.session.commit()
        return jsonify(
            {
                "code": 200,
                "data": {
                    "id": id
                }
            }
        )
    return jsonify(
        {
            "code": 404,
            "data": {
                "id": id
            },
            "message": "User not found."
        }
    ), 404


if __name__ == '__main__':
    app.run(port=5000, debug=True)
