import os
import json
import pandas as pd

import psycopg2
from flask import jsonify
from psycopg2.extras import RealDictCursor

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

DB_SERVER = os.environ['DB_SERVER']
DB_NAME = os.environ['DB_NAME']
DB_USER = os.environ['DB_USER']
DB_PASSWORD = os.environ['DB_PASSWORD']

conn = psycopg2.connect(host=DB_SERVER, database=DB_NAME,
                        user=DB_USER, password=DB_PASSWORD)


def get_rated_movie_ids(user_id):
    '''Get a list of movie IDs a user has rated'''
    query = """SELECT movie.movie_id FROM movie, rating WHERE rating.user_id = {user_id} AND movie.movie_id = rating.movie_id;""".format(
        user_id=user_id)
    df = pd.read_sql(query, conn)
    return df['movie_id'].apply(int).tolist()


def get_movies(ids):
    id_list = "','".join(ids)
    query = "SELECT * FROM movie WHERE movie_id IN ('" + id_list + "');"
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(query)
    result = cur.fetchall()
    data = json.dumps(result, default=str, indent=2)
    return json.loads(data)[:]
