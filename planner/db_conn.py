from psycopg2.pool import ThreadedConnectionPool
import json

# Import app config
config = json.load(open('config.json'))

# Setup `psycopg` connection, http://initd.org/psycopg/docs/usage.html
connPool = ThreadedConnectionPool(1, 10,
    host=config.get('dbHost'),
    dbname=config.get('dbName'),
    user=config.get('dbUser'),
    password=config.get('dbPass'),
    port=config.get('dbPort')
)
# cur = conn.cursor()

# print('Testing DB connection...')
# cur.execute('SELECT 1')
# cur.fetchone()
# print('Test successful!')

# print('\nFetching spatial data from DB...')
# cur.execute(
#     """SELECT admin, ST_Y(ST_Centroid(wkb_geometry)) as latitude
#        FROM ne_110m_admin_0_countries
#        ORDER BY latitude
#        DESC LIMIT 10;
#        """)
# rows = cur.fetchall()
# print('Done!')
# print('\nData returned by the database')
# for row in rows:
#     print(row)


# # Commit changes to the database (if any) and close connection
# conn.commit()
# cur.close()
# conn.close()
