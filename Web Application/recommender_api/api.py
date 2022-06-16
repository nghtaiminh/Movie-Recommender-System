from flask import Flask, jsonify, request
from flask_cors import CORS

from crud import *
from matrixfactorization import MF
from tfidf import * 


app = Flask(__name__)
app.secret_key = '11111'
cors =  CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type' 


#  Load ML models
try:
    mf_model = MF.load_model('./model/mf')
    tfidf_model = loadTFIDF('./model/tfidf')
except Exception:
    print("Can't load the models")

@app.route("/api/recommend", methods=['GET'])
def recommend():
    bundle = request.args.get('bundle')
    
    if bundle == 'personalized_recommendation':
        user_id = request.args.get('user_id')
        limit = request.args.get('limit')
        rated_movie_ids = get_rated_movie_ids(user_id)
        recommended_ids = mf_model.recommend(int(user_id), rated_movie_ids, int(limit))
        recommended_ids = recommended_ids['item_id'].apply(str).tolist()
        result = get_movies(recommended_ids)


    elif bundle == 'similar_recommendation':
        movie_id = request.args.get('movie_id')
        limit = request.args.get('limit')
        recommended_ids =  tfidf_model.recommend(target_id = int(movie_id), numRecommendation=12)
        recommended_ids = map(str, recommended_ids)
        result = get_movies(recommended_ids)

    return jsonify(success=True, statusCode=200, data=result, errors=None)




@app.route("/api/update_model")
def update_model():
    user_id = request.args.get('user_id')
    movie_id = request.args.get('movie_id')
    rating = request.args.get('rating')

    user_item = pd.DataFrame(
                data={'user_id': [int(user_id)], 'item_id': [int(movie_id)]})

    rating = pd.Series(data=[float(rating)])
    try:
        # update the  model with old data
        mf_model.update(user_item, rating)
        # save the model
        mf_model.save_model('./model/mf')
        return jsonify(success=True, message="The model is updated")
    except Exception:
        return jsonify(success=False, message="Can't update the model")

    



if __name__ ==  '__main__':
    app.run(host="127.0.0.1", port="5000", debug=True)