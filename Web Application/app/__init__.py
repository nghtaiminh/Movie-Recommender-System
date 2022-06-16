import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_session import  Session
# from flask_script import Manager

# from config import Config, BASE_DIR
db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    return app
