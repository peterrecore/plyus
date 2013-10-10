from flask import Flask, render_template
from flask.ext.sqlalchemy import SQLAlchemy

from plyus import app
from plyus import db
from plyus.gamestate import GameState

@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/games')
def list_games():
    app.logger.warn("entered list_ games")
    games = GameState.query.all()
    app.logger.warn("got games")
    s = ""
    for g in games:
        x = ("%s, %s , %s \n") %(g.id, g.stage, g.step)
        s+=(x)
    app.logger.info("about to return")
    return render_template("sample.html",title="purple", games = games ) 

@app.route('/hello')
def hello():
    app.logger.warn("about to say hello")
    return 'hello works fine'