
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

__all__ = ["player","referee", "gamestate","errors","util","round","misc"]

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = SQLAlchemy(app)

from plyus import misc, gamestate, round 
from plyus import webapp