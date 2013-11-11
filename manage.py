#!python
from flask.ext import script
import plyus
import config

plyus.create_flask_app(config.dev)
manager = script.Manager(plyus.app)


@manager.command
def create_db():
    from plyus import db

    db.create_all()


@manager.command
def run():
    plyus.app.run(debug=True)


if __name__ == "__main__":
    manager.run()
