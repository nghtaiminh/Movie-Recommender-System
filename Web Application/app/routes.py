import pandas as pd

from flask import request, Flask, render_template, redirect, url_for,  jsonify, session, flash, request
from werkzeug.security import generate_password_hash, check_password_hash
import requests

from crud import *
from utils import *

app = Flask(__name__)
app.secret_key = '12345'


@app.route('/')
def root():
    if 'user_id' not in session:
        n_rated_movies = 0
        personalized_recommendations = get_random_movies()
    else:
        n_rated_movies = get_number_of_rated_movies(session['user_id'])

        # 10 is the number of movies the user need to rate before being recommended
        if n_rated_movies >= 10:
            # Call recommendation API
            params = {'bundle': 'personalized_recommendation',
                      'user_id': session['user_id'], 'limit': 12}
            res = requests.get(
                'http://127.0.0.1:5000/api/recommend', params=params).json()
            personalized_recommendations = res['data']

        else:
            personalized_recommendations = get_random_movies()

    top_rated_movies = get_top_rated_movie()
    new_release_movies = get_new_release_movies()

    return render_template('home.html', top_rated_movies=top_rated_movies,
                           new_release_movies=new_release_movies,
                           top_picks_or_random_movies=personalized_recommendations,
                           n_rated_movies=n_rated_movies)


@app.route("/login/", methods=['GET', 'POST'])
def login():

    error = ''
    if request.method == 'POST':
        username = str(request.form.get('username')).strip()
        password = str(request.form.get('password')).strip()

        user = get_a_user(username)
        print(user)

        if user:
            if check_password_hash(user['password'], password):
                session.clear()
                session['logged_in'] = True
                session['username'] = user['username']
                session['user_id'] = user['user_id']
                flash('You were logged in', category='success')
                return redirect(url_for('root'))
            else:
                error = "Incorrect password!"
        else:
            error = "Username not found!"

    return render_template('login.html', error=error)


@app.route("/profile/")
def profile():
    rated_movies = get_rated_movies(session['user_id'])

    return render_template('profile.html', rated_movies=rated_movies)


@app.route('/register/', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        username = str(request.form.get('username')).strip()
        password = str(request.form.get('password')).strip()

        # Check if the username is already registered
        if get_a_user(username):
            flash('Username is already exists!', 'warning')
        else:
            # Hash the password
            hashed_password = generate_password_hash(password, method='sha256')
            # Insert the user into the database
            insert_user(username, hashed_password)
            # Store the session
            user = get_a_user(username)
            session['logged_in'] = True
            session['username'] = user[1]
            session['user_id'] = user[0]
            flash(f'Your account has been created!')
            return redirect(url_for('root'))

    return render_template('register.html')


@app.route("/logout/")
def logout():
    session.clear()
    # flash('You have been logged out', 'success')
    return redirect(url_for('root'))


@app.route('/search', methods=['POST'])
def search():
    search_terms = str(request.form.get('search_terms')).strip()
    return redirect(url_for('result', page=1, search_terms=search_terms))


@app.route('/result', methods=['GET', 'POST'])
def result():
    search_terms = request.args.get('search_terms')
    page = request.args.get('page')
    results = search_movie(search_terms, int(page)-1)
    return render_template('searchResult.html', results=results,
                           search_terms=search_terms,
                           page=page)


@app.route('/movies/<movie_id>')
def movies(movie_id):
    movie_details = get_movie(movie_id)
    genres = get_genres(movie_id)
    rating = 0

    if 'user_id' in session:
        # Check if the user has rated this movie
        check_rating = get_rating_from_user(session['user_id'], movie_id)
        if check_rating:
            rating = check_rating[0]['rating']

    # Send request to recommendation api
    params = {'bundle': 'similar_recommendation',
              'movie_id': movie_id, 'limit': 12}
    res = requests.get('http://127.0.0.1:5000/api/recommend',
                       params=params).json()
    similar_movies = res['data']

    return render_template('movieDetails.html', movie_details=movie_details,
                           similar_movies=similar_movies,
                           rating=rating,
                           genres=genres)


@app.route('/movies/<movie_id>/rates/', methods=['POST', 'GET'])
def rates(movie_id):
    if 'user_id' not in session:
        flash('Please login before rating!')
        return jsonify(dict(redirect='/login/'))
    else:
        if request.method == 'POST':
            rating = request.form.get('rating')
            insert_or_update_rating(session['user_id'], movie_id, rating)

            # Send request to update the model with new data
            params = {'movie_id': movie_id,
                      'user_id': session['user_id'], 'rating': rating}
            requests.get('http://127.0.0.1:5000/api/update_model',
                         params=params).json()

            movie_details = get_movie(movie_id)
            params = {'bundle': 'similar_recommendation',
                      'movie_id': movie_id, 'limit': 12}
            res = requests.get(
                'http://127.0.0.1:5000/api/recommend', params=params).json()
            similar_movies = res['data']

            return render_template('movieDetails.html', movie_details=movie_details,
                                   similar_movies=similar_movies)


@app.route('/movies/<movie_id>/rates/delete/', methods=['DELETE'])
def rates_delete(movie_id):
    if 'user_id' not in session:
        return jsonify(dict(redirect='/login/'))
    else:
        delete_rating(session['user_id'], movie_id)
        return jsonify(success=True, message="The rating is deleted")


@app.route('/dashboard/', methods=['GET'])
def dashboard():
    chart1_data = frequency_of_rating(
        get_frequency_of_rating(session['user_id']))
    chart2_data = n_rating_per_genre(
        get_num_of_movies_per_genre(session['user_id']))
    chart3_data = decade_distribution(
        get_decade_distribution_of_rated_movies(session['user_id']))
    chart4_data = avg_rating_per_genre(
        get_avg_rating_each_genre(session['user_id']))
    n_rated_movies = get_number_of_rated_movies(session['user_id'])

    return render_template('dashboard.html', chart1_data=chart1_data,
                           chart2_data=chart2_data,
                           chart3_data=chart3_data,
                           chart4_data=chart4_data,
                           n_rated_movies=n_rated_movies)


if __name__ == '__main__':
    app.run(debug=True, host="127.0.0.1", port=3000)
