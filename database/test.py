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
        ID SERIAL PRIMARY KEY,
        firstname VARCHAR(150),
        lastname VARCHAR(150),
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

# works until here and creates the table

sql = "INSERT INTO public.users (firstname, lastname, birthdate, age, date_joined, preferences, desiredFirstDate, mbti, pass, email) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"

values = [("John", "Smith", "1990-03-09", 30, "2022-08-12", ["sporty", "outdoors"], ["outdoors", ""], "infp", "password123"), ("Jane", "Lee", "1999-05-12", 24, "2023-01-12", ["homebody", "indoors"], "intp", "password123")]

# query1 = cur.executemany(sql,values)

# Commit the transaction
conn.commit()

query2 = cur.execute(
    "SELECT * from public.users"
).fetchall()

print(query2)

# Close the cursor and connection
cur.close()
conn.close()