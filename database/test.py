import psycopg

conn_params = {
    'host':"flirtify-4040.6xw.cockroachlabs.cloud",
    'port':"26257",
    'dbname':"flirtify",
    'user':"jeremy",
    'password':"GvtUwDUhQOYrlDC7jEbblg",
}
 
conn = psycopg.connect(**conn_params)

# Open a cursor to execute SQL commands
cur = conn.cursor()

# Execute the SQL command to create a new database
cur.execute("SET DATABASE = flirtify")

run_sql('''
    CREATE TABLE IF NOT EXISTS public.users (
        ID SERIAL PRIMARY KEY,
        firstname VARCHAR(150) NOT NULL,
        lastname VARCHAR(150) NOT NULL,
        gender varchar(1) not null,
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
    
    sql = "INSERT INTO public.users (firstname, lastname, gender, birthdate, age, date_joined, preferences, desiredFirstDate, mbti, pass, email) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

    values = [("John", "Smith", "M", "1990-03-09", 30, "2022-08-12", ["sporty", "outdoors"], ["rock-climbing"], "infp", "password123", "johnsmith@gmail.com"),
              ("Joel", "Dong", "M", "1942-01-01", 99, "2022-01-01", ["sporty", "outdoors", "gym", "teamfight tactics", "monkey shoulder"], ["rock-climbing", "teamfight tactics", "deadlift competition", "haidilao"], "enfj", "password123", "joeldong@gmail.com"),
               ("Jane", "Lee", "F","1999-05-12", 24, "2023-01-12", ["homebody", "indoors"], ["cafe", "arcade"], "intp", "password123", "janelee@gmail.com"),
               ("Jada", "Tan", "F", "2001-06-06", 21, "2023-01-12", ["homebody", "indoors", "cooking", "drinking", "spending money", "steak"], ["haidilao"],"infp", "password123", "jadatan@coral.com"),
                ("Alison", "Bong", "F", "1999-05-12", 21, "2023-01-12", ["sporty", "indoors"],["crocheting", "deadlift competition"], "enfj", "password123", "abong@bong.com")]

    query1 = get_conn().cursor().executemany(sql,values)
    app.logger.info('user table set up, test data inputted')
res = cur.execute('''
    DROP TABLE IF EXISTS public.users;
    CREATE TABLE IF NOT EXISTS public.users (
        ID SERIAL PRIMARY KEY,
        firstname VARCHAR(150),
        lastname VARCHAR(150),
        gender VARCHAR(1),
        birthdate DATE,
        age INT,
        date_joined DATE,
        preferences TEXT[],
        desiredFirstDate TEXT[],
        MBTI VARCHAR(4),
        pass VARCHAR(64),
        email VARCHAR(256)
    )
    ''')

sql = "INSERT INTO public.users (firstname, lastname, birthdate, age, date_joined, preferences, desiredFirstDate, mbti, pass, email) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"

values = [
("John", "Smith", "1990-03-09", 30, "2022-08-12", ["sporty", "outdoors"], ["outdoors", ""], "infp", "password123"), 
("Jane", "Lee", "1999-05-12", 24, "2023-01-12", ["homebody", "indoors"], "intp", "password123"),
("Jada", "Tan", "F", "2001-06-06", 21, "2023-01-12", ["homebody", "outdoors", "cooking", "drinking"], "infp", "password123"),
("Alison", "Bong", "F", "1999-05-12", 21, "2023-01-12", ["sporty", "indoors"], "enfj", "password123")
]


cur.executemany(sql,values)

# Commit the transaction
conn.commit()

users = cur.execute(
    "SELECT * from public.users"

).fetchall()

for user in users:
    print(user)

# Close the cursor and connection
cur.close()
conn.close()