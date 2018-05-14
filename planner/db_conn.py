from psycopg2.pool import ThreadedConnectionPool
from config import config

# Setup `psycopg` connection, http://initd.org/psycopg/docs/usage.html
connPool = ThreadedConnectionPool(1, 10,
                                  host=config.get('dbHost'),
                                  dbname=config.get('dbName'),
                                  user=config.get('dbUser'),
                                  password=config.get('dbPass'),
                                  port=config.get('dbPort'))
