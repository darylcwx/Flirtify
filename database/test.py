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

res = cur.execute('''
    DROP TABLE IF EXISTS public.users;
    CREATE TABLE IF NOT EXISTS public.users (
        ID INT PRIMARY KEY,
        firstname VARCHAR(150),
        lastname VARCHAR(150),
        gender VARCHAR(1),
        birthdate DATE,
        age INT,
        date_joined DATE,
        preferences TEXT[],
        MBTI VARCHAR(4),
        pass VARCHAR(64)
    )
    ''')

sql = "INSERT INTO public.users (id, firstname, lastname, gender, birthdate, age, date_joined, preferences, mbti, pass) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

values = [(1, "John", "Smith", "M","1990-03-09", 30, "2022-08-12", ["sporty", "outdoors"], "infp", "password123"),
          (2, "Jane", "Lee", "F", "1999-05-12", 24, "2023-01-12", ["homebody", "indoors"], "intp", "password123"),
          (3, "Jada", "Tan", "F", "2001-06-06", 21, "2023-01-12", ["homebody", "outdoors", "cooking", "drinking"], "infp", "password123"),
          (4, "Alison", "Bong", "F", "1999-05-12", 21, "2023-01-12", ["sporty", "indoors"], "enfj", "password123"),]

cur.executemany(sql,values)

# Commit the transaction
conn.commit()

users = cur.execute(
    "SELECT * from public.users"
)
for user in users:
    print(user)

# Close the cursor and connection
cur.close()
conn.close()