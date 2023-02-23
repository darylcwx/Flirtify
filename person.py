from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/person'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

CORS(app)  

class Person(db.Model):
    __tablename__ = 'person'

    id = db.Column(db.String(13), primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    price = db.Column(db.Float(precision=2), nullable=False)
    availability = db.Column(db.Integer)

    def __init__(self, isbn13, title, price, availability):
        self.isbn13 = isbn13
        self.title = title
        self.price = price
        self.availability = availability

    def json(self):
        return {"id": self.id, "name": self.name, "price": self.price, "availability": self.availability}


@app.route("/person")
def get_all():
    persons = Person.query.all()
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
    person = Person.query.filter_by(id=id).first()
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
    if (Person.query.filter_by(id=id).first()):
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
    person = Person(id, **data)

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
    person = Person.query.filter_by(id=id).first()
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
    person = Person.query.filter_by(id=id).first()
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
