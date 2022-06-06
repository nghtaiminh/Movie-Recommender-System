# Movie Recommendation System



## Installation

To run locally:

### Environment + Packages Installation

- install python 3
- install virtualenv
- virtualenv -p python3 venv
- source venv/bin/activate
- pip install -r requirements.txt

### Database Installation

- Create a database with PostgreSQL
- Restore the database with `backup.sql` file.
- Go to `Web Application/app/CRUD.py` and change the database configuration.

### Model Preparation

- Go to `recommender_module` folder, run notebook `matrixfactorization.ipynb` and `TF_IDF.ipynb`

### Run the project

- cd app/
- python app.py

Then go to:  http://127.0.0.1:3000/



The recommendation algorithms is not built from scratch,

Ref 
- TMDB API

