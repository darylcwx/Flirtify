from flask import Flask, jsonify, request, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from itsdangerous import exc
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

conn_string = "postgresql://jeremy:GvtUwDUhQOYrlDC7jEbblg@flirtify-4040.6xw.cockroachlabs.cloud:26257/flirtify.flirtify?sslmode=verify-full"

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.config['SQLALCHEMY_DATABASE_URI'] = conn_string
app.config['SECRET_KEY'] = 'flirtify_esd_micro'
app.config['SESSION_COOKIE_DOMAIN'] = '127.0.0.1'
app.config['SESSION_COOKIE_PATH'] = '/'
db = SQLAlchemy(app)
CORS(app)

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
    desiredfirstdate = db.Column(db.String)
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
    
    # return "Hello, World!"
    return render_template('home.html')

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
    
@app.route("/user/gender/<string:gender>")
def get_all_opp_gender(gender):
    user_search = session.query(User).filter_by(gender=gender).all()
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
            "message": "There are no users with that gender."
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
    user = User(email=email, **data)
    
    # session.add(user)
    # session.commit()
    
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

@app.route("/user/<string:userid>", methods=['DELETE'])
def delete_user(userid):
    user = session.query(User).filter_by(id=userid).first()
    if user:
        session.delete(user)
        session.commit()
        return jsonify(
            {
                "code": 200,
                "data": {
                    "id": userid
                },
                "message": "User successfully deleted."
            }
        )
    return jsonify(
        {
            "code": 404,
            "data": {
                "id": userid
            },
            "message": "User not found."
        }
    ), 404
    
@app.route("/user/<string:userid>", methods=['PUT'])
def update_user(userid):
    user_search = session.query(User).filter_by(id=userid).first()
    try:
        if user_search:
            data = request.get_json()
            if data['firstname'] is not None:
                user_search.firstname = data['firstname']
            else:
                data['firstname'] = user_search.firstname
            if data['lastname'] is not None:
                user_search.lastname = data['lastname']
            else:
                data['lastname'] = user_search.lastname
            if data['gender'] is not None:
                user_search.gender = data['gender']
            else:
                data['gender'] = user_search.gender
            if data['birthdate'] is not None:
                user_search.birthdate = data['birthdate']
            else:
                data['birthdate'] = user_search.birthdate
            if data['age'] is not None:
                user_search.age = data['age']
            else:
                data['age'] = user_search.age
            if data['date_joined'] is not None:
                user_search.date_joined = data['date_joined']
            else:
                data['date_joined'] = user_search.date_joined
            if data['preferences'] is not None:
                user_search.preferences = data['preferences']
            else:
                data['preferences'] = user_search.preferences
            if data['desiredfirstdate'] is not None:
                user_search.desiredfirstdate = data['desiredfirstdate']
            else:
                data['desiredfirstdate'] = user_search.desiredfirstdate
            if data['mbti'] is not None:
                user_search.mbti = data['mbti']
            else:
                data['mbti'] = user_search.mbti
            if data['email'] is not None:
                user_search.email = data['email']
            else:
                data['email'] = user_search.email
            if data['password'] is not None:
                user_search.password = data['password']
            else:
                data['password'] = user_search.password
            session.commit()
            return jsonify(
                {
                    "code": 200,
                    "data": user_search.json()
                }
            )
        return jsonify(
        {
            "code": 404,
            "data": {
                "id": userid
            },
            "message": "User not found."
        }
        ), 404
    except:
        return jsonify(
            {
                "code": 500,
                "data": {
                    "userid": userid
                },
                "message": "An error occurred updating the user."
            }
        ), 500

@app.context_processor
def inject_navbar():
    return dict(navbar="navbar.html")
            

if __name__ == '__main__':
    app.run(port=26257, debug=True)