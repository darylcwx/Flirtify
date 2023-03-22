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

sql = 'INSERT INTO public.match (user_id1, user_id2, user1_match, user2_match, "datePrefs", "dateIdea") VALUES (%s, %s, %s, %s, %s, %s)'

values = [(100, 200, False, False, None, None), (848395333569937409, 848395333575245825, None, None, None, None), (848395333572722689, 848395333577605121, False, None, None, None)]

# cur.executemany(sql,values)

# cur.execute("DELETE FROM public.match where match_id='849163053037486081'")

# Commit the transaction
conn.commit()

matches = cur.execute("SELECT * FROM public.match").fetchall()

for match in matches:
    print(match)
    
# msgs = cur.execute("SELECT * FROM public.messages").fetchall()

# for msg in msgs:
#     print(msg)