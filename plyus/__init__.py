from config import basedir
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.openid import OpenID

import os

db = None
app = None
lm = None
oid = None

def create_flask_app(my_config):
    global app, db, lm, oid

    app = Flask(__name__)
    app.config.update(my_config)

    db = SQLAlchemy(app)
    lm = LoginManager()
    lm.init_app(app)
    lm.login_view = 'login'
    lm.login_message = 'Please log in to access this page.'

    oid = OpenID(app, os.path.join(basedir, 'tmp'))

    from plyus import misc, gamestate, round, player, user, proto
    from plyus import webapp