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


def get_a_user(username: str, password: str):
    query = """SELECT * FROM "user" WHERE username = %s AND password = %s;"""
    cur = conn.cursor()
    cur.execute(query, (username, password))
    result = cur.fetchone()
    cur.close()
    return result

def get_username(username: str):
    query = """SELECT * FROM "user" WHERE username = %s;"""
    cur = conn.cursor()
    cur.execute(query, (username,))
    result = cur.fetchone()
    cur.close()
    return result


def get_rating_from_user(user_id, movie_id):
    '''Get rating of a user for a movie'''
    query = """SELECT rating
                FROM rating, movie 
                WHERE movie.movie_id = rating.movie_id AND rating.user_id = %s AND rating.movie_id = %s;"""
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(query, (user_id, movie_id))
    result = cur.fetchall()
    cur.close()
    data = json.dumps(result, sort_keys=True, default=str)
    return json.loads(data)


def get_movies(ids):
    id_list = "','".join(ids)
    query = "SELECT * FROM movie WHERE movie_id IN ('" + id_list + "');"
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(query)
    result = cur.fetchall()
    data = json.dumps(result, default=str, indent=2)
    return json.loads(data)[:]


def get_top_rated_movie():
    '''Get 12 movies with the most 5-star rated that user hasn't watched '''
    query = """ SELECT movie.movie_id, title, movie.poster_path, counter
                FROM movie
                JOIN (SELECT movie_id, COUNT(*) AS counter FROM rating 
	                WHERE rating = 5
	                GROUP BY movie_id 
	                ORDER BY counter DESC 
	                LIMIT 12) t
                ON movie.movie_id = t.movie_id;"""
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(query)
    result = cur.fetchall()
    data = json.dumps(result, default=str)
    return json.loads(data)


def get_random_movies(user_id='-1'):
    '''Get 12 random movies that user hasn't rated'''
    query = """SELECT *
                FROM movie
                WHERE movie_id NOT IN (
	                SELECT rating.movie_id 
	                FROM movie, rating
	                WHERE rating.user_id = %s AND movie.movie_id = rating.movie_id)
                ORDER BY RANDOM() LIMIT 12;"""
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(query, (user_id,))
    result = cur.fetchall()
    data = json.dumps(result, default=str)
    return json.loads(data)


def get_new_release_movies(user_id='-1'):
    '''Get 12 newest release date movies'''
    query = """ SELECT * 
                FROM movie
                ORDER BY release_date DESC 
                LIMIT 12;"""
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(query, (user_id,))
    result = cur.fetchall()
    data = json.dumps(result, default=str)
    return json.loads(data)


def get_movie(movie_id):
    '''Get details of a movie'''
    query = """SELECT * FROM movie WHERE movie_id = %s;"""
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(query, (movie_id,))
    result = cur.fetchall()
    data = json.dumps(result, sort_keys=True, default=str)
    return json.loads(data)


def get_number_of_rated_movies(user_id):
    query = """SELECT COUNT(*) FROM movie, rating WHERE rating.user_id = %s AND movie.movie_id = rating.movie_id;"""
    cur = conn.cursor()
    cur.execute(query, (user_id,))
    result = cur.fetchall()
    return result[0][0]


def get_rated_movies(user_id):
    '''Get all the movies a user has rated'''
    query = """SELECT movie.movie_id, title ,rating, imdb_id, movie.poster_path
                FROM rating, movie 
                WHERE movie.movie_id = rating.movie_id AND rating.user_id = %s;"""
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(query, (user_id,))
    result = cur.fetchall()

    data = json.dumps(result)
    return json.loads(data)


def get_rated_movie_ids(user_id):
    '''Get a list of movie IDs a user has rated'''
    query = """SELECT movie.movie_id FROM movie, rating WHERE rating.user_id = {user_id} AND movie.movie_id = rating.movie_id;""".format(
        user_id=user_id)
    df = pd.read_sql(query, conn)
    return df['movie_id'].apply(int).tolist()


def get_frequency_of_rating(user_id):
    '''Get the frequency for all rating of a user'''
    query = """ WITH rating_freq AS 
	            (SELECT 
                    rating.rating, 
                    COUNT(rating) AS frequency 
	            FROM (SELECT * FROM rating WHERE rating.user_id = %s) AS rating
	            GROUP BY rating
	            ORDER BY rating
                )
                SELECT 
                    generate_series as rating, 
                    COALESCE(frequency, 0) AS frequency
                FROM generate_series(0, 5, 0.5)
                LEFT JOIN rating_freq ON generate_series = rating_freq.rating;"""
    cur = conn.cursor()
    cur.execute(query, (user_id,))
    result = cur.fetchall()
    data = json.dumps(result, default=str)
    return json.loads(data)


def insert_or_update_rating(user_id, movie_id, rating):
    query = """UPDATE rating SET rating = %(rating)s, timestamp = CAST(EXTRACT(epoch FROM NOW()) AS INT)  WHERE user_id = %(user_id)s AND movie_id = %(movie_id)s;
                INSERT INTO rating(user_id, movie_id, rating, timestamp) 
		        SELECT %(user_id)s, %(movie_id)s,  %(rating)s, CAST(EXTRACT(epoch FROM NOW()) AS INT)
		        WHERE NOT EXISTS (SELECT 1 FROM rating WHERE user_id=%(user_id)s AND movie_id= %(movie_id)s);"""
    cur = conn.cursor()
    cur.execute(query, {'rating': rating,
                'user_id': user_id, 'movie_id': movie_id})
    conn.commit()
    return cur.statusmessage


def delete_rating(user_id, movie_id):
    query = """DELETE FROM rating WHERE user_id = %(user_id)s AND movie_id = %(movie_id)s;"""
    cur = conn.cursor()
    cur.execute(query, {'user_id': user_id, 'movie_id': movie_id})
    conn.commit()
    return cur.statusmessage


def get_num_of_movies_per_genre(user_id):
    query = """ WITH genre_counter AS (
	                SELECT genre.genre_name, COUNT(movie_genre.movie_id) AS counter
	                FROM genre 
	                LEFT JOIN movie_genre ON movie_genre.genre_id = genre.genre_id
	                WHERE movie_genre.movie_id IN (
		                SELECT movie.movie_id 
		                FROM rating, movie 
		                WHERE rating.user_id = %s AND rating.movie_id = movie.movie_id)
	                GROUP BY genre.genre_id, genre.genre_name
                )
                SELECT genre.genre_name, COALESCE(counter, 0) AS counter
                FROM genre
                LEFT JOIN genre_counter ON genre_counter.genre_name = genre.genre_name;"""
    cur = conn.cursor()
    cur.execute(query, (user_id,))
    result = cur.fetchall()
    data = json.dumps(result, default=str)
    return json.loads(data)


def get_decade_distribution_of_rated_movies(user_id='-1'):
    query = """SELECT dist_group, count(*)
                FROM (
                    SELECT CASE
	                when EXTRACT(YEAR FROM release_date ) < 1970 then '< 1970s'
	                when EXTRACT(YEAR FROM release_date ) between 1970 and 1979 then '1970s'
	                when EXTRACT(YEAR FROM release_date ) between 1980 and 1989 then '1980s'
	                when EXTRACT(YEAR FROM release_date ) between 1990 and 1999 then '1990s'
	                when EXTRACT(YEAR FROM release_date ) between 2000 and 2009 then '2000s'
	                when EXTRACT(YEAR FROM release_date ) between 2010 and 2020 then '2010s'
	                end AS dist_group
	                FROM movie
	                WHERE movie_id IN (
		                SELECT rating.movie_id 
		                FROM movie, rating
		                WHERE rating.user_id = %s AND movie.movie_id = rating.movie_id)
                ) t
                GROUP BY dist_group
                ORDER BY dist_group ASC;"""
    cur = conn.cursor()
    cur.execute(query, (user_id,))
    result = cur.fetchall()
    data = json.dumps(result)
    return json.loads(data)


def get_avg_rating_each_genre(user_id='-1'):
    query = """SELECT genre.genre_name, ROUND(AVG(rating.rating)::NUMERIC,2)
                FROM genre  
				LEFT JOIN movie_genre ON movie_genre.genre_id = genre.genre_id
				LEFT JOIN rating ON movie_genre.movie_id = rating.movie_id
                WHERE movie_genre.movie_id IN (
	                SELECT movie.movie_id 
	                FROM rating, movie 
	                WHERE rating.user_id = %s AND rating.movie_id = movie.movie_id)
                GROUP BY genre.genre_id, genre.genre_name;"""
    cur = conn.cursor()
    cur.execute(query, (user_id,))
    result = cur.fetchall()
    data = json.dumps(result, default=str)
    return json.loads(data)


def insert_user(username, password):
    query = """INSERT INTO "user" (username, password) VALUES (%s, %s);"""
    cur = conn.cursor()
    cur.execute(query, (username, password))
    conn.commit()
    return cur.statusmessage


def search_movie(search_terms, page):
    '''Get all the movie that the title contains a term'''
    query = """SELECT * FROM movie WHERE title ILIKE %(search_terms)s OFFSET %(page)s*8 LIMIT 8;"""
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(query, {"search_terms": '%'+search_terms+'%', "page": page})
    result = cur.fetchall()
    data = json.dumps(result, default=str)
    return json.loads(data)


def get_genres(movie_id):
    '''Get all the genres of a movie'''
    query = """SELECT genre_name
                FROM genre, movie_genre 
                WHERE genre.genre_id=movie_genre.genre_id AND movie_genre.movie_id = %s;"""
    cur = conn.cursor()
    cur.execute(query, (movie_id,))
    result = [r[0] for r in cur.fetchall()]
    return result
