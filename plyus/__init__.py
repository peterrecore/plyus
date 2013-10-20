from config import basedir
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.openid import OpenID
import os

__all__ = ["player","referee", "gamestate","errors","util","round","misc"]

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
app.config['CSRF_ENABLED']= True
app.config['SECRET_KEY'] = '42'
app.config['OPENID_PROVIDERS'] = [
    { 'name': 'Google', 'url': 'https://www.google.com/accounts/o8/id' },
    { 'name': 'Yahoo', 'url': 'https://me.yahoo.com' },
    { 'name': 'MyOpenID', 'url': 'https://www.myopenid.com' }]

db = SQLAlchemy(app)
lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'
lm.login_message = 'Please log in to access this page.'

oid = OpenID(app, os.path.join(basedir, 'tmp'))

from plyus import misc, gamestate, round, player, user
from plyus import webapp