from flask import request, Flask, render_template, redirect, url_for,  jsonify, session, flash, request, Blueprint


import pandas as pd

# Import CRUD file 
from CRUD import *

# Import the model
from matrixfactorization import MF
from tfidf import *


app = Flask(__name__)
app.secret_key = '12345'

#  Load ML models
try:
    mf_model = MF.load_model('./recommender_module/model/mf')
    tfidf_model = loadTFIDF('./recommender_module/model/tfidf')
except Exception:
    print("Can't load the models")

def personalized_recommendation(user_id, rated_movie_ids):
    result = mf_model.recommend(user_id, rated_movie_ids, 12)
    return result['item_id'].apply(str).tolist()


def similar_movies_recommendations(movie_id):
    result = tfidf_model.recommendate(
        target_id=int(movie_id), numRecommendation=12)
    return map(str, result)


@app.route('/')
def root():
    if 'user_id' not in session:
        n_rated_movies = 0
        top_rated_movies = get_top_rated_movie()
        new_release_movies = get_new_release_movies()
        top_picks_or_random_movies = get_random_movies()
    # Get top rating
    else:
        n_rated_movies = get_number_of_rated_movies(session['user_id'])

        # 10 is the number of movies the user need to rate before being recommended
        if n_rated_movies >= 10:
            # Display Rate More section
            rated_movie_ids = get_rated_movie_ids(session['user_id'])
            recommended_movie_ids = personalized_recommendation(
                session['user_id'], rated_movie_ids)
            top_picks_or_random_movies = get_movies(recommended_movie_ids)

        else:
            top_picks_or_random_movies = get_random_movies()
        top_rated_movies = get_top_rated_movie(session['user_id'])
        new_release_movies = get_new_release_movies(session['user_id'])


    return render_template('home.html', top_rated_movies=top_rated_movies, 
                                        new_release_movies=new_release_movies, 
                                        top_picks_or_random_movies=top_picks_or_random_movies, 
                                        n_rated_movies=n_rated_movies)


@app.route("/login/", methods=['GET', 'POST'])
def login():

    error = ''
    if request.method == 'POST':
        username = str(request.form.get('username')).strip()
        password = str(request.form.get('password')).strip()
        user = get_a_user(username, password)

        if user is None:
            error = 'Incorrect username or password!'

        if error == '':
            session.clear()
            session['logged_in'] = True
            session['username'] = user[1]
            session['user_id'] = user[0]
            return redirect(url_for('root'))

        flash(error, 'warning')
    else:
        return render_template('login.html')

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
        if get_a_user(username, password):
            flash(f'Username is already exists', 'warning')
        else:
            insert_user(username, password)
            user = get_a_user(username, password)
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
                           search_terms=search_terms, page=page)


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
    similar_movie_ids = similar_movies_recommendations(movie_id)
    similar_movies = get_movies(similar_movie_ids)
    return render_template('movieDetails.html', movie_details=movie_details, similar_movies=similar_movies, rating=rating, genres=genres)


@app.route('/movies/<movie_id>/rates/', methods=['POST', 'GET'])
def rates(movie_id):
    if 'user_id' not in session:
        flash('Please login before rating!')
        return jsonify(dict(redirect='/login/'))
    else:
        if request.method == 'POST':
            rating = request.form.get('rating')
            insert_or_update_rating(session['user_id'], movie_id, rating)
            user_item = pd.DataFrame(
                data={'user_id': [int(session['user_id'])], 'item_id': [int(movie_id)]})
            float_rating = pd.Series(data=[float(rating)])
            print(user_item)
            print(float_rating)
            # Update and save the model
            mf_model.update(user_item, float_rating)
            mf_model.save_model('./recommender_module/model/mf')

            movie_details = get_movie(movie_id)
            similar_movie_ids = similar_movies_recommendations(movie_id)
            similar_movies = get_movies(similar_movie_ids)
            return render_template('movieDetails.html', movie_details=movie_details, similar_movies=similar_movies)


@app.route('/movies/<movie_id>/rates/delete/', methods=['DELETE'])
def rates_delete(movie_id):
    if 'user_id' not in session:
        return jsonify(dict(redirect='/login/'))
    else:
        delete_rating(session['user_id'], movie_id)
        return "sucess"


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

    return render_template('dashboard.html', chart1_data=chart1_data, chart2_data=chart2_data, chart3_data=chart3_data,  chart4_data=chart4_data, n_rated_movies=n_rated_movies)



def frequency_of_rating(db_data):
    data = {'0.5': 0, '1.0': 0, '1.5': 0, '2.0': 0, '2.5': 0,
            '3.0': 0, '3.5': 0, '4.0': 0, '4.5': 0, '5.0': 0}
    # data = {0.5: 0, 1.0: 0, 1.5: 0, 2.0: 0, 2.5: 0,
    #         3.0: 0, 3.5: 0, 4.0: 0, 4.5: 0, 5.0: 0}
    for key, value in db_data:
        data[str(key)] = value
    return str(data)


def n_rating_per_genre(db_data):
    data = {'Action': 0, 'Adventure': 0, 'Animation': 0, 'Comedy': 0, 'Crime': 0, 'Documentary': 0, 'Drama': 0, 'Family': 0, 'Fantasy': 0, 'Foreign': 0,
            'History': 0, 'Horror': 0, 'Music': 0, 'Mystery': 0, 'Romance': 0, 'Science Fiction': 0, 'Thriller': 0, 'TV Movie': 0, 'War': 0, 'Western': 0}

    for key, value in db_data:
        data[key] = value
    return data


def avg_rating_per_genre(db_data):
    data = {'Action': 0, 'Adventure': 0, 'Animation': 0, 'Comedy': 0, 'Crime': 0, 'Documentary': 0, 'Drama': 0, 'Family': 0, 'Fantasy': 0, 'Foreign': 0,
            'History': 0, 'Horror': 0, 'Music': 0, 'Mystery': 0, 'Romance': 0, 'Science Fiction': 0, 'Thriller': 0, 'TV Movie': 0, 'War': 0, 'Western': 0}
    for key, value in db_data:
        data[key] = float(value)
    return data


def decade_distribution(db_data):
    data = {'< 1970s': 0, '1970s': 0, '1980s': 0,
            '1990s': 0, '2000s': 0, '2010s': 0}
    for key, value in db_data:
        data[key] = value
    return data

if __name__ == '__main__':
    app.run(debug=True, host="127.0.0.1", port=3000)