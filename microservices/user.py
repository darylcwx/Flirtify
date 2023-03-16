from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

conn_string = "postgresql://jeremy:GvtUwDUhQOYrlDC7jEbblg@flirtify-4040.6xw.cockroachlabs.cloud:26257/flirtify.flirtify?sslmode=verify-full"

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = conn_string
db = SQLAlchemy(app)
# CORS(app)

# Configure the SQLAlchemy engine to use CockroachDB
engine = create_engine('cockroachdb+psycopg2://jeremy:GvtUwDUhQOYrlDC7jEbblg@flirtify-4040.6xw.cockroachlabs.cloud:26257/flirtify?sslmode=require')

# Create a SQLAlchemy session factory to manage database connections
Session = sessionmaker(bind=engine)

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(150), nullable=False)
    lastname = db.Column(db.String(150), nullable=False)
    gender = db.Column(db.String(1), nullable=False)
    birthdate = db.Column(db.Date, nullable=False)
    age = db.Column(db.Integer, nullable=False)
    date_joined = db.Column(db.Date)
    preferences = db.Column(db.ARRAY(db.String))
    desiredfirstdate = db.Column(db.ARRAY(db.String))
    mbti = db.Column(db.String(4))
    email = db.Column(db.String(256))
    password = db.Column(db.String)
    
    def __init__(self, firstname, lastname, gender, birthdate, age, date_joined, preferences, desiredfirstdate, mbti, email, password):
        self.firstname = firstname
        self.lastname = lastname
        self.gender = gender
        self.birthdate = birthdate
        self.age = age
        self.date_joined = date_joined
        self.preferences = preferences
        self.desiredfirstdate = desiredfirstdate
        self.mbti = mbti
        self.email = email
        self.password = password
        
    def json(self):
        result = {"id":self.id, "firstname":self.firstname, "lastname":self.lastname, "gender":self.gender, "birthdate":self.birthdate, "age":self.age, "date_joined":self.date_joined, "preferences":self.preferences, "desiredfirstdate":self.desiredfirstdate, "mbti":self.mbti, "email":self.email}
        return result
        

@app.route('/')
def index():
    
    return "Hello, World!"

session = Session()

@app.route("/user")
def get_all():
    user_search = session.query(User).all()
    if len(user_search):
        return jsonify(
            {
                "code": 200,
                "data": {
                    "users": [user.json() for user in user_search]
                }
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "There are no users."
        }
    ), 404

@app.route("/user/<string:userid>")
def get_user(userid):
    user_search = session.query(User).filter_by(id=userid).first()
    if (user_search):
        return jsonify(
            {
                "code": 200,
                "data": user_search.json()
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "User not found."
        }
    ), 404
    
@app.route("/user/create/<string:email>", methods=['POST'])
def create_user(email):
    # replaced_email = str(email).replace('@', '%40').replace('.', '%2E')
    user_search = session.query(User).filter_by(email=email).first()
    if (user_search):
        return jsonify(
            {
                "code": 400,
                "data": user_search.json(),
                "message": "User already exists."
            }
        ), 400
        
    data = request.get_json()
    user = User(**data)
    
    session.add(user)
    session.commit()
    
    try:
        session.add(user)
        session.commit()
    except:
        return jsonify(
            {
                "code": 500,
                "data": {
                    "email": email
                },
                "message": "An error occurred creating the user."
            }
        ), 500
        
    return jsonify(
    {
        "code": 201,
        "data": user.json()
    }
    ), 201


if __name__ == '__main__':
    app.run(port=26257, debug=True)