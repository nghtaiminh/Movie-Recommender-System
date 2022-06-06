# for recommender
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import pickle


def conv(val):
    try:
        return int(val)
    except:
        return -1

# convert to json to return the result through http


def to_json(recommend_list: list()):
    movie_dict = {}
    for i, movie_id in enumerate(recommend_list):
        movie_dict[str(i)] = str(movie_id)
    return movie_dict


def loadTFIDF(savePath):
    """
        savePath (str): * do not include ".pickle"
    """
    file_to_read = open(savePath + ".pickle", "rb")
    tfidf = pickle.load(file_to_read)
    file_to_read.close()
    return tfidf


class MOVIE_TFIDF:

    def __init__(self, dataPath=None, savePath=None, nrows=None):
        """
            savePath (str): path of the saved MOVIE_TFIDF, not includes '.pickle' 
        """
        # to load the existing tfidf
        if savePath is not None:
            self = loadTFIDF(savePath)
        else:
            self._data = self.__readData(dataPath, nrows=nrows)
            self._tfidf_matrix = self.__computeTFIDFmatrix(self._data['tfidf'])
            self.movieid_index = self._data['id']
            del self._data
            self._cosine_sim = self.__computeSimilarity(self._tfidf_matrix)
            del self._tfidf_matrix

    def __readData(self, dataPath, nrows):
        movies_tfidf = pd.read_csv(dataPath, nrows=nrows, dtype={
                                   'title': str, 'genres': str}, converters={'id': conv})
        # drop na and dups
        movies_tfidf.dropna(how="any", inplace=True)
        movies_tfidf.drop_duplicates(inplace=True)
        # title + genre + overview
        genres = movies_tfidf['genres']
        title = movies_tfidf['title']
        overview = movies_tfidf['overview']
        movies_tfidf['tfidf'] = genres + '|' + title + "|" + overview
        # set index
        movies_tfidf.index = range(len(movies_tfidf))
        return movies_tfidf

    def __computeTFIDFmatrix(self, movieGenres):
        tf = TfidfVectorizer(analyzer='word', ngram_range=(
            1, 2), min_df=0, stop_words='english')
        tfidf_matrix = tf.fit_transform(movieGenres)
        return tfidf_matrix

    def __computeSimilarity(self, tfidf_matrix):
        cosine_sim = cosine_similarity(
            X=tfidf_matrix, Y=tfidf_matrix, dense_output=False)
        return cosine_sim

    def recommendate(self, target_id: int, rated_movie_id: list() = None, numRecommendation=10) -> list():
        """
            target_id (int): the movie's id that needs recommendation
            numRecommendation (int): number of recommend movies, default = 10
            return list(): list of recommend ids
        """
        if any(self.movieid_index.isin([target_id])) is True:
            print('Target id is exists')
        else:
            return ['Target id is not exists']
        recommendLists = []
        # get the index of the target movie
        movie_index = self.movieid_index[self.movieid_index == target_id].index
        print('The target index: ', movie_index)
        print('the target id in data: ', self.movieid_index.loc[movie_index])
        # get all similarities of the target movie and the others
        movie_sims = self._cosine_sim[movie_index, :].toarray()[0]
        # sort by sim but get indexes only
        sorted_indexes = np.argsort(movie_sims)
        # find most similar movies
        for i in sorted_indexes:
            if (movie_sims[i] != 1.0 and numRecommendation > 0):
                # append the movie's ids
                candidate_movie_id = self.movieid_index.loc[i]
                # avoid rated movies
                if (rated_movie_id is not None) and (candidate_movie_id in rated_movie_id):
                    continue
                recommendLists.append(candidate_movie_id)
                numRecommendation -= 1
            else:
                break
        return recommendLists

    def saveTFIDF(self, savePath):
        """
            savePath (str): * do not include ".pickle"
        """
        file_to_store = open(savePath + ".pickle", "wb")
        pickle.dump(self, file_to_store, protocol=4)
        file_to_store.close()
