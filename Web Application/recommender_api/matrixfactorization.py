# Data manipulation
import numpy as np
import pandas as pd

# Modeling
from matrix_factorization import KernelMF, train_update_test_split
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split

# Other
import os
import random

# Saving model
import pickle

rand_seed = 2
np.random.seed(rand_seed)
random.seed(rand_seed)

NUM_EPOCHS = 50
UPDATE_N_EPOCHS = 20


DATA_PATH = './data/Rating.csv'
COL_NAMES = ['user_id', 'item_id', 'rating']


def read_data(data_path, col_names):
    return pd.read_csv(data_path, header=0, names=col_names, usecols=[0, 1, 2])


def split_train_test(dataframe):
    X = dataframe[['user_id', 'item_id']]
    y = dataframe['rating']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
    return (X_train, X_test, y_train, y_test)


def read_data(data_path, col_names):
    return pd.read_csv(data_path, header=0, names=col_names, usecols=[0, 1, 2])


def split_train_test(dataframe):
    X = dataframe[['user_id', 'item_id']]
    y = dataframe['rating']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
    return (X_train, X_test, y_train, y_test)


class MF:
    def __init__(self, X_train, y_train, num_epochs=NUM_EPOCHS, save_model_path=None):
        """
            save_model_path (str): * do not include ".pickle"
            * if save_model_path is not none, other parameters do not need any values
        """
        if save_model_path is None:
            self.model = self.__train(X_train, y_train, num_epochs)
        else:
            self = MF.load_model(save_model_path)

    def __train(self, X_train, y_train, num_epochs):
        matrix_fact = KernelMF(n_epochs=num_epochs,
                               n_factors=100, verbose=1, lr=0.001, reg=0.005)
        matrix_fact.fit(X_train, y_train)
        return matrix_fact

    def update(self, new_X_train: pd.DataFrame, new_y_train: pd.Series, n_epochs=UPDATE_N_EPOCHS):
        """
            new_X_train: a dataframe with two cols: user_id, item_id
            new_y_train: a series of rating corresponds to new_X_train
        """
        self.model.update_users(new_X_train, new_y_train,
                                lr=0.001, n_epochs=n_epochs, verbose=1)

    def evaluate(self, X_test, y_test):
        """
            compute RMSE on test data
        """
        pred = self.model.predict(X_test)
        rmse = mean_squared_error(y_test, pred, squared=False)
        print(f'\nTest RMSE: {rmse:.4f}')

    def recommend(self, user_id, items_known, numMovie: int):
        return self.model.recommend(user=user_id, items_known=items_known, amount=numMovie)

    def save_model(self, save_path):
        """
            savePath (str): * do not include ".pickle"
        """
        file_to_store = open(save_path + ".pickle", "wb")
        pickle.dump(self, file_to_store)
        file_to_store.close()

    def load_model(save_path):
        """
            savePath (str): * do not include ".pickle"
        """
        file_to_read = open(save_path + ".pickle", "rb")
        mf = pickle.load(file_to_read)
        file_to_read.close()
        return mf
