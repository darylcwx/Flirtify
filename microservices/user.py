import psycopg
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

conn_string = "postgresql://jeremy:GvtUwDUhQOYrlDC7jEbblg@flirtify-4040.6xw.cockroachlabs.cloud:26257/flirtify.flirtify?sslmode=verify-full"

conn_params = {
    'host':"flirtify-4040.6xw.cockroachlabs.cloud",
    'port':"26257",
    'dbname':"flirtify",
    'user':"jeremy",
    'password':"GvtUwDUhQOYrlDC7jEbblg",
}

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = conn_string
db = SQLAlchemy(app)
CORS(app)

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(150), nullable=False)
    lastname = db.Column(db.String(150), nullable=False)
    birthdate = db.Column(db.Date, nullable=False)
    age = db.Column(db.Integer, nullable=False)
    preferences = db.Column(db.ARRAY(db.String))
    desiredFirstDate = db.Column(db.ARRAY(db.String))
    mbti = db.Column(db.String(4))
    email = db.Column(db.String(256))
    
    def __init__(self, firstname, lastname, birthdate, age, preferences, desiredFirstDate, mbti, email):
        self.firstname = firstname
        self.lastname = lastname
        self.birthdate = birthdate
        self.age = age
        self.preferences = preferences
        self.desiredFirstDate = desiredFirstDate
        self.mbti = mbti
        self.email = email

def get_conn():
    conn = psycopg.connect(**conn_params, autocommit=True)
    return conn

def run_sql(sql):
    with get_conn() as txn:
        txn.execute(sql)
        
def json(info):
    result = {"id":info[0], "firstname":info[1], "lastname":info[2], "birthdate":info[3], "age":info[4], "date_joined":info[5], "preferences":info[6], "desiredFirstDate":info[7], "mbti":info[8], "email":info[10]}
    return result
        

@app.route('/')
def index():
    run_sql('''
    CREATE TABLE IF NOT EXISTS public.users (
        ID SERIAL PRIMARY KEY,
        firstname VARCHAR(150) NOT NULL,
        lastname VARCHAR(150) NOT NULL,
        birthdate DATE NOT NULL,
        age INT NOT NULL,
        date_joined DATE NOT NULL,
        preferences TEXT[] ,
        desiredFirstDate TEXT[],
        MBTI VARCHAR(4),
        pass VARCHAR(64) NOT NULL,
        email VARCHAR(256) NOT NULL
    )
    ''')
    
    sql = "INSERT INTO public.users (firstname, lastname, birthdate, age, date_joined, preferences, desiredFirstDate, mbti, pass, email) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

    values = [("John", "Smith", "1990-03-09", 30, "2022-08-12", ["sporty", "outdoors"], ["rock-climbing"], "infp", "password123", "johnsmith@gmail.com"),
              ("Joel", "Dong", "1942-01-01", 99, "2022-01-01", ["sporty", "outdoors", "gym", "teamfight tactics", "monkey shoulder"], ["rock-climbing", "teamfight tactics", "deadlift competition", "haidilao"], "enfj", "password123", "joeldong@gmail.com"),
               ("Jane", "Lee", "1999-05-12", 24, "2023-01-12", ["homebody", "indoors"], ["cafe", "arcade"], "intp", "password123", "janelee@gmail.com"),
               ("Jada", "Tan", "F", "2001-06-06", 21, "2023-01-12", ["homebody", "indoors", "cooking", "drinking", "spending money", "steak"], ["haidilao"],"infp", "password123", "jadatan@coral.com"),
                ("Alison", "Bong", "F", "1999-05-12", 21, "2023-01-12", ["sporty", "indoors"],["crocheting", "deadlift competition"], "enfj", "password123", "abong@bong.com")]

    query1 = get_conn().cursor().executemany(sql,values)
    app.logger.info('user table set up, test data inputted')
    return "Hello, World!"

@app.route("/user")
def get_all():
    user_search = get_conn().cursor().execute("SELECT * from public.users").fetchall()
    if len(user_search):
        return jsonify(
            {
                "code": 200,
                "data": {
                    "users": [json(user) for user in user_search]
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
    user_search = get_conn().cursor().execute("SELECT * from public.users WHERE id = %s",(userid,)).fetchone()
    if (user_search):
        return jsonify(
            {
                "code": 200,
                "data": json(user_search)
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "User not found."
        }
    ), 404
    
app.route("/user/create/<string:email>", methods=['POST'])
def create_user(email):
    user_search = get_conn().cursor().execute("SELECT * from public.users WHERE email = %s",(email,)).fetchone()
    if (user_search):
        return jsonify(
            {
                "code": 400,
                "data": json(user_search),
                "message": "User already exists."
            }
        ), 400
        
    data = request.get_json()
    user = User(**data)
    
    try:
        db.session.add(user)
        db.session.commit()
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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=26257, debug=True)