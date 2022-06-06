

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