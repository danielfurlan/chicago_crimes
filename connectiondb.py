import sqlite3
from sqlite3 import Error


# SQLITE
def create_connection_sqlite(db):
    """ create a database connection to a database that resides
        in the memory
    """
    conn = None;
    try:
        conn = sqlite3.connect(db,timeout= 15,check_same_thread=False)
        print(sqlite3.version)
        print("Connection to sqlite db successful!")
        return conn
    except Error as e:
        print(e)
    #finally:
        #if conn:
            #conn.close()

def execute_read_query_sqlite(connection, query):
    cur = connection.cursor()
    result = None
    try:
        cur.execute(query)
        result = cur.fetchall()
        column_n = cur.description
        #connection.commit()
        return result, column_n
    except OperationalError as e:
        print("The error {} occurred".format(e))


### POSTGRESQL
#@retry(wait=wait_exponential(multiplier=2, min=1, max=10), stop=stop_after_attempt(5))
def create_connection(db_name, db_user, db_password, db_host, db_port):
    connection = None
    try:
        connection = psycopg2.connect(
            database=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
        )
        print("Connection to PostgreSQL DB successful")
    except OperationalError as e:
        print("The error {} occurred".format(e))
    return connection


def execute_read_query(connection, query):
    cursor = connection.cursor()
    result = None
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        column_n = cursor.description
        return result, column_n
    except OperationalError as e:
        print("The error {} occurred".format(e))


